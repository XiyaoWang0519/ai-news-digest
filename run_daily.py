import datetime, json, pathlib, os
from collectors.google_ai_rss import GoogleAIRSCollector
from collectors.openai_news import OpenAINewsCollector
from digester import store
from digester.summariser import create_digest


def main():
    collectors = [
        OpenAINewsCollector(),
        GoogleAIRSCollector(),
        # …add Anthropic etc. later
    ]

    total = 0
    for col in collectors:
        items = col.fetch_items()
        store.save_batch(items)
        print(f"[{col.source_name}] {len(items)} items")
        total += len(items)

    print(f"Saved {total} items in total.")

    # Generate daily digest
    try:
        today_rows = store.get_recent_items(int(os.getenv("MAX_STORIES", 12)))
        if today_rows:
            digest = create_digest(today_rows, datetime.date.today())
            
            # Save digest to output directory
            out_dir = pathlib.Path("output")
            out_dir.mkdir(exist_ok=True)
            out_path = out_dir / f"{digest['date']}.json"
            out_path.write_text(json.dumps(digest, indent=2, ensure_ascii=False))
            print(f"✓ Daily digest written to {out_path}")
        else:
            print("No items found for digest generation.")
    except Exception as e:
        print(f"Error generating digest: {e}")


if __name__ == "__main__":
    main()
