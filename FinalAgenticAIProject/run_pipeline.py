from src.pipeline import run_pipeline


if __name__ == "__main__":
    result = run_pipeline()
    print("Pipeline completed.")
    print(f"Tickets generated: {len(result['tickets'])}")
    print("Output files written to outputs/")
