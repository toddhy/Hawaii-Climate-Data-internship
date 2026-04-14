# HCDP TIFF Downloader Guide

The `tiff_downloader.py` script is a command-line utility for batch downloading GeoTIFF raster data from the [Hawaii Climate Data Portal (HCDP)](https://api.hcdp.ikewai.org/).

## Features

- **Multi-Resolution Support**: Download both monthly (`YYYY-MM`) and daily (`YYYY-MM-DD`) datasets.
- **Variable Selection**: Supports rainfall, temperature, and other variables via the `--datatype` flag.
- **Batch Processing**: Automatically iterates through date ranges and saves files locally.
- **Authentication**: Uses `HCDP_API_TOKEN` for secure access.

## Setup

1. **API Token**: Obtain an API token from the HCDP website.
2. **Environment Variables**: Create a `.env` file in the project root or the `HCDP_API` directory:
   ```env
   HCDP_API_TOKEN=your_token_here
   ```
3. **Dependencies**: Ensure you have the required libraries installed:
   ```bash
   pip install requests python-dotenv python-dateutil
   ```

## Usage

### Monthly Data
To download monthly rainfall data for the year 2022:
```bash
python tiff_downloader.py 2022-01 2022-12 --output_dir downloads/monthly
```

### Daily Data
To download daily rainfall maps for the first week of 2026:
```bash
python tiff_downloader.py 2026-01-01 2026-01-07 --output_dir downloads/daily
```

## Command-Line Arguments

| Argument | Description | Default |
| :--- | :--- | :--- |
| `start_date` | Starting date of the range (YYYY-MM or YYYY-MM-DD). | Required |
| `end_date` | Ending date of the range (YYYY-MM or YYYY-MM-DD). | Required |
| `--datatype` | The climate variable to download (e.g., `rainfall`, `temperature`). | `rainfall` |
| `--output_dir` | Local directory to save the TIFF files. | `downloads` |

## Technical Details

- **Daily vs. Monthly Detection**: The script automatically detects the date format based on length. It sets the API's `period` parameter to `day` for 10-character dates and `month` for 7-character dates.
- **Iterative Logic**:
    - For daily ranges, it uses `timedelta(days=1)` to step through the sequence.
    - For monthly ranges, it uses `relativedelta(months=1)` to correctly handle varying month lengths.
- **Retry Handling**: The script uses `stream=True` for memory-efficient downloads of large raster files.

---
> [!NOTE]
> When downloading `rainfall` data, the script automatically appends the `production=new` parameter to the API request to ensure the latest processed datasets are retrieved.
