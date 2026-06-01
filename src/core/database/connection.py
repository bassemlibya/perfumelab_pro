import sqlite3
import os
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager
import threading

# إعداد التسجيل (logging)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseError(Exception):
    """استثناء مخصص لأخطاء قاعدة البيانات"""
    pass

class DatabaseManager:
    """مدير قاعدة البيانات - نسخة واحدة (Singleton Thread-Safe)"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, db_path: str = None):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, db_path: str = None):
        """تهيئة مدير قاعدة البيانات (مرة واحدة فقط)"""
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self._db_path = db_path or "perfumelab.db"
        self._connection_pool = {}
        self._thread_local = threading.local()
        self._initialized = True
        
        # التأكد من وجود المجلدات اللازمة
        db_dir = os.path.dirname(self._db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
        
        logger.info(f"DatabaseManager initialized with path: {self._db_path}")
    
    def get_connection(self) -> sqlite3.Connection:
        """الحصول على اتصال بقاعدة البيانات (الاتصال خاص بالـ thread)"""
        if not hasattr(self._thread_local, 'connection') or self._thread_local.connection is None:
            try:
                conn = sqlite3.connect(
                    self._db_path,
                    check_same_thread=False,  # للـ threads المختلفة
                    timeout=20.0,  # وقت الانتظار للقفل
                    isolation_level=None  # الوضع التلقائي للمعاملات
                )
                conn.row_factory = sqlite3.Row
                
                # إعدادات محسنة للأداء والأمان
                conn.execute("PRAGMA foreign_keys = ON")
                conn.execute("PRAGMA journal_mode = WAL")
                conn.execute("PRAGMA synchronous = NORMAL")
                conn.execute("PRAGMA cache_size = -2000")  # 2MB cache
                conn.execute("PRAGMA temp_store = MEMORY")
                conn.execute("PRAGMA mmap_size = 268435456")  # 256MB
                
                self._thread_local.connection = conn
                logger.debug(f"New database connection created for thread: {threading.current_thread().name}")
            except sqlite3.Error as e:
                logger.error(f"Failed to create database connection: {e}")
                raise DatabaseError(f"فشل الاتصال بقاعدة البيانات: {e}")
        
        return self._thread_local.connection
    
    def close_connection(self):
        """إغلاق اتصال الـ thread الحالي"""
        if hasattr(self._thread_local, 'connection') and self._thread_local.connection:
            try:
                self._thread_local.connection.close()
                logger.debug(f"Database connection closed for thread: {threading.current_thread().name}")
            except Exception as e:
                logger.warning(f"Error closing connection: {e}")
            finally:
                self._thread_local.connection = None
    
    @contextmanager
    def transaction(self):
        """إدارة المعاملات (بداية - Commit - Rollback)"""
        conn = self.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE")  # قفل فوري للمعاملة
            yield conn
            conn.commit()
            logger.debug("Transaction committed successfully")
        except Exception as e:
            conn.rollback()
            logger.error(f"Transaction rolled back due to error: {e}")
            raise DatabaseError(f"فشل تنفيذ المعاملة: {e}") from e
    
    def execute(self, query: str, params: Tuple = ()) -> List[Dict]:
        """تنفيذ استعلام SELECT وإرجاع النتائج"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(query, params)
                results = [dict(row) for row in cursor.fetchall()]
                logger.debug(f"Query executed: {query[:100]}... returned {len(results)} rows")
                return results
        except sqlite3.Error as e:
            logger.error(f"Query execution failed: {query[:100]}... Error: {e}")
            raise DatabaseError(f"فشل تنفيذ الاستعلام: {e}") from e
    
    def execute_one(self, query: str, params: Tuple = ()) -> Optional[Dict]:
        """تنفيذ استعلام SELECT وإرجاع صف واحد"""
        results = self.execute(query, params)
        return results[0] if results else None
    
    def execute_insert(self, query: str, params: Tuple = ()) -> int:
        """تنفيذ استعلام INSERT وإرجاع المعرف الجديد"""
        conn = self.get_connection()
        try:
            cursor = conn.execute(query, params)
            conn.commit()
            last_id = cursor.lastrowid
            logger.debug(f"Insert executed, last row id: {last_id}")
            return last_id
        except sqlite3.Error as e:
            logger.error(f"Insert failed: {query[:100]}... Error: {e}")
            raise DatabaseError(f"فشل إدخال البيانات: {e}") from e
    
    def execute_update(self, query: str, params: Tuple = ()) -> int:
        """تنفيذ استعلام UPDATE/DELETE وإرجاع عدد الصفوف المتأثرة"""
        conn = self.get_connection()
        try:
            cursor = conn.execute(query, params)
            conn.commit()
            affected_rows = cursor.rowcount
            logger.debug(f"Update executed, affected rows: {affected_rows}")
            return affected_rows
        except sqlite3.Error as e:
            logger.error(f"Update failed: {query[:100]}... Error: {e}")
            raise DatabaseError(f"فشل تحديث البيانات: {e}") from e
    
    def execute_many(self, query: str, params_list: List[Tuple]) -> int:
        """تنفيذ استعلام متعدد (Batch Insert/Update)"""
        conn = self.get_connection()
        try:
            with self.transaction() as conn:
                cursor = conn.executemany(query, params_list)
            total_rows = cursor.rowcount
            logger.info(f"Batch executed: {total_rows} rows affected")
            return total_rows
        except sqlite3.Error as e:
            logger.error(f"Batch execution failed: {e}")
            raise DatabaseError(f"فشل تنفيذ العملية المجمعة: {e}") from e
    
    def execute_script(self, script: str) -> bool:
        """تنفيذ سكربت SQL كامل (للتهيئة)"""
        conn = self.get_connection()
        try:
            with self.transaction() as conn:
                conn.executescript(script)
            logger.info("Script executed successfully")
            return True
        except sqlite3.Error as e:
            logger.error(f"Script execution failed: {e}")
            raise DatabaseError(f"فشل تنفيذ السكربت: {e}") from e
    
    def initialize_database(self, schema_path: str = None) -> bool:
        """تهيئة قاعدة البيانات من ملف الـ schema"""
        try:
            # البحث عن ملف الـ schema في عدة مسارات
            if schema_path is None:
                schema_path = self._find_schema_file()
            
            if not os.path.exists(schema_path):
                raise FileNotFoundError(f"Schema file not found: {schema_path}")
            
            # التحقق إذا كانت قاعدة البيانات موجودة
            if os.path.exists(self._db_path):
                logger.info(f"Database already exists: {self._db_path}")
                # التحقق من وجود الجداول
                return self._verify_tables()
            
            # قراءة وتنفيذ الـ schema
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = f.read()
            
            logger.info(f"Creating database from schema: {schema_path}")
            self.execute_script(schema)
            logger.info(f"Database created successfully: {self._db_path}")
            return True
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise DatabaseError(f"فشل تهيئة قاعدة البيانات: {e}") from e
    
    def _find_schema_file(self) -> str:
        """البحث عن ملف الـ schema في المسارات المتوقعة"""
        current_file = os.path.abspath(__file__)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
        
        possible_paths = [
            os.path.join(project_root, 'schema.sql'),  # مسار مباشر في الجذر
            os.path.join(project_root, 'src', 'database', 'schema.sql'),
            os.path.join(os.path.dirname(current_file), 'schema.sql'),
            os.path.join(os.path.dirname(current_file), 'migrations', '001_initial_schema.sql'),
            os.path.join(project_root, 'database', 'schema.sql'),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"Schema file found at: {path}")
                return path
        
        raise FileNotFoundError(f"No schema file found in: {possible_paths}")
    
    def _verify_tables(self) -> bool:
        """التحقق من وجود الجداول الأساسية"""
        try:
            tables = self.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            if len(tables) < 10:  # الحد الأدنى للجداول المهمة
                logger.warning(f"Database has only {len(tables)} tables, may need re-initialization")
                return False
            logger.info(f"Database verification passed: {len(tables)} tables found")
            return True
        except Exception as e:
            logger.error(f"Database verification failed: {e}")
            return False
    
    def backup(self, backup_path: str = None) -> str:
        """إنشاء نسخة احتياطية من قاعدة البيانات"""
        try:
            if not backup_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_dir = "backups"
                if not os.path.exists(backup_dir):
                    os.makedirs(backup_dir)
                backup_path = os.path.join(backup_dir, f"perfumelab_backup_{timestamp}.db")
            
            # إغلاق أي اتصال مفتوح قبل النسخ
            self.close_connection()
            
            # نسخ قاعدة البيانات
            source_conn = sqlite3.connect(self._db_path)
            dest_conn = sqlite3.connect(backup_path)
            
            try:
                source_conn.backup(dest_conn)
                logger.info(f"Backup created successfully: {backup_path}")
                return backup_path
            finally:
                source_conn.close()
                dest_conn.close()
                
        except sqlite3.Error as e:
            logger.error(f"Backup failed: {e}")
            raise DatabaseError(f"فشل إنشاء النسخة الاحتياطية: {e}") from e
    
    def restore(self, backup_path: str) -> bool:
        """استعادة قاعدة البيانات من نسخة احتياطية"""
        if not os.path.exists(backup_path):
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        
        try:
            # إغلاق جميع الاتصالات
            self.close_connection()
            
            # نسخ الملف الاحتياطي إلى الموقع الأصلي
            import shutil
            shutil.copy2(backup_path, self._db_path)
            
            logger.info(f"Database restored from: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            raise DatabaseError(f"فشل استعادة النسخة الاحتياطية: {e}") from e
    
    def vacuum(self) -> bool:
        """إعادة تنظيم قاعدة البيانات وتقليل حجمها"""
        try:
            self.execute("VACUUM")
            logger.info("Database vacuumed successfully")
            return True
        except sqlite3.Error as e:
            logger.error(f"Vacuum failed: {e}")
            return False
    
    def get_table_info(self, table_name: str) -> List[Dict]:
        """الحصول على معلومات عن هيكل الجدول"""
        return self.execute(f"PRAGMA table_info({table_name})")
    
    def table_exists(self, table_name: str) -> bool:
        """التحقق من وجود جدول"""
        result = self.execute_one(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        return result is not None
    
    def __enter__(self):
        """دعم Context Manager"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """إغلاق الاتصال عند الخروج"""
        self.close_connection()
    
    def __del__(self):
        """التنظيف عند حذف الكائن"""
        try:
            self.close_connection()
        except:
            pass

# دالة مساعدة لإنشاء مدير قاعدة البيانات بسهولة
def get_db_manager(db_path: str = None) -> DatabaseManager:
    """الحصول على نسخة واحدة من مدير قاعدة البيانات"""
    return DatabaseManager(db_path)

# مثال الاستخدام
if __name__ == "__main__":
    # اختبار بسيط
    db = DatabaseManager("test.db")
    
    try:
        # إنشاء جدول اختبار
        db.execute_script("""
            CREATE TABLE IF NOT EXISTS test (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
        """)
        
        # إدراج بيانات
        db.execute_insert("INSERT INTO test (name) VALUES (?)", ("PerfumeLab",))
        
        # استعلام
        result = db.execute_one("SELECT * FROM test WHERE id = ?", (1,))
        print(f"Test result: {result}")
        
        # نسخ احتياطي
        db.backup()
        
    finally:
        # تنظيف
        db.execute("DROP TABLE IF EXISTS test")
