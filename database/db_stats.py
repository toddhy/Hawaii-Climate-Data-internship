import os
import json
import tiledb

def get_array_stats(array_uri):
    try:
        with tiledb.DenseArray(array_uri, mode='r') as array:
            time_mapping = json.loads(array.meta["time_mapping"])
            dates = sorted(time_mapping.keys())
            
            if not dates:
                return {
                    "Name": os.path.basename(array_uri),
                    "Count": 0,
                    "Range": "N/A",
                    "Resolution": f"{array.meta['height']}x{array.meta['width']}"
                }
            
            start_date = dates[0]
            end_date = dates[-1]
            
            # Determine if it's daily or monthly based on the first date string
            is_daily = len(start_date.split('-')) == 3
            
            return {
                "Name": os.path.basename(array_uri),
                "Type": "Daily" if is_daily else "Monthly",
                "Count": len(dates),
                "Start": start_date,
                "End": end_date,
                "Resolution": f"{array.meta['height']}x{array.meta['width']}"
            }
    except Exception as e:
        return {
            "Name": os.path.basename(array_uri),
            "Error": str(e)
        }

def main():
    db_dir = os.path.dirname(os.path.abspath(__file__))
    arrays = [
        "rainfall_array",
        "temperature_array",
        "max_temp_array",
        "min_temp_array",
        "spi_array",
        "2026_daily_rainfall",
        "daily_rainfall_optimized"
    ]
    
    stats = []
    for array_name in arrays:
        uri = os.path.join(db_dir, array_name)
        if os.path.exists(uri):
            stats.append(get_array_stats(uri))
        else:
            stats.append({"Name": array_name, "Error": "Not Found"})
            
    # Print the results
    print("\n" + "="*80)
    print(" HCDP TILEDB DATABASE STATISTICS ".center(80, "="))
    print("="*80 + "\n")
    
    header = ["Array Name", "Type", "Count", "Start Date", "End Date", "Resolution"]
    rows = []
    for s in stats:
        if "Error" in s:
            rows.append([s["Name"], "ERROR", "-", "-", "-", s["Error"]])
        else:
            rows.append([
                s["Name"],
                s["Type"],
                s["Count"],
                s["Start"],
                s["End"],
                s["Resolution"]
            ])
            
    # Try to use tabulate for pretty printing, fallback to simple formatting
    try:
        from tabulate import tabulate
        print(tabulate(rows, headers=header, tablefmt="grid"))
    except ImportError:
        # Simple manual formatting
        print(f"{'Array Name':<25} {'Type':<10} {'Count':<6} {'Start':<12} {'End':<12} {'Resolution':<15}")
        print("-" * 80)
        for r in rows:
            print(f"{str(r[0]):<25} {str(r[1]):<10} {str(r[2]):<6} {str(r[3]):<12} {str(r[4]):<12} {str(r[5]):<15}")

if __name__ == "__main__":
    main()
