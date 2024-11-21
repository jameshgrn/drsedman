from setuptools import setup, find_packages

setup(
    name="mlx-rag",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "mlx>=0.0.8",
        "duckdb>=0.9.2",
        "transformers>=4.36.2",
        "google-generativeai>=0.3.2",
        "python-dotenv>=1.0.0",
        "tqdm>=4.66.1",
    ],
    entry_points={
        "console_scripts": [
            "mccode=scripts.mccode:main",
            "process-pdfs=scripts.process_pdfs_gemini:main",
            "process-embeddings=scripts.process_and_embed:main",
        ],
    },
) 