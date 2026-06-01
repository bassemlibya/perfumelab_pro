from setuptools import setup, find_packages

setup(
    name="perfumelab-pro",
    version="2.0.0",
    description="ERP/POS System for Perfume Manufacturing and Retail",
    author="PerfumeLab",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "PySide6>=6.5.0",
        "qrcode>=7.4.2",
        "Pillow>=10.0.0",
        "openpyxl>=3.1.2",
        "reportlab>=4.0.4",
        "python-barcode>=1.3.0",
    ],
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "perfumelab=main_app:main",
        ],
    },
)
