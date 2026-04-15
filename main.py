import os
import sys
import webbrowser

from config import FIRECRAWL_API_KEY, OPENAI_API_KEY, MODEL_NAME, BRANDS, OUTPUT_PATH
from agent import TrendAgent


def main():
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY environment variable not set.")
        print("  export OPENAI_API_KEY=sk-...")
        sys.exit(1)

    if not FIRECRAWL_API_KEY:
        print("Error: FIRECRAWL_API_KEY not configured.")
        sys.exit(1)

    agent = TrendAgent(
        brands=BRANDS,
        firecrawl_api_key=FIRECRAWL_API_KEY,
        openai_api_key=OPENAI_API_KEY,
        model_name=MODEL_NAME,
        output_path=OUTPUT_PATH,
    )

    report = agent.run()

    total_products = sum(len(br.products) for br in report.brand_reports)
    print(f"\n{'='*60}")
    print(f"Report complete!")
    print(f"  Brands    : {len(report.brand_reports)}")
    print(f"  Products  : {total_products}")
    print(f"  Output    : {OUTPUT_PATH}")
    print(f"{'='*60}\n")

    abs_path = os.path.abspath(OUTPUT_PATH)
    print(f"Opening report in browser: file://{abs_path}")
    webbrowser.open(f"file://{abs_path}")


if __name__ == "__main__":
    main()
