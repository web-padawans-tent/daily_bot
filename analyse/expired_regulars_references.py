import csv

if __name__ == "__main__":
    references = []
    # читаємо регулярки
    with open("expired_regulars.csv", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("orderReference"):
                references.append(row['orderReference'])

    print(references)
    with open("expired_regulars_references.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=['orderReference'])
        writer.writeheader()
        writer.writerows(references)

    print(
        f"✅ Готово: записано {len(references)} прострочених регулярок у expired_regulars.csv")
