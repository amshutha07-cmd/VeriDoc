from pathlib import Path
import requests

FILES = [
    ('https://s2.q4cdn.com/470004039/files/doc_earnings/2023/q4/filing/_10-K-Q4-2023-As-Filed.pdf', 'data/corporate_filings/apple_fy2023_10k.pdf' ),
    ('https://s2.q4cdn.com/470004039/files/doc_earnings/2024/q4/filing/10-Q4-2024-As-Filed.pdf', 'data/corporate_filings/apple_fy2024_10k.pdf' ),
    ('https://cdn-dynmedia-1.microsoft.com/is/content/microsoftcorp/MSFT_FY25q4_10K', 'data/corporate_filings/microsoft_fy2025_10k.docx' ),
    ('https://s201.q4cdn.com/141608511/files/doc_financials/2025/annual/NVIDIA-2025-Annual-Report.pdf', 'data/corporate_filings/nvidia_fy2025_annual_report.pdf' ),
    ('https://s2.q4cdn.com/299287126/files/doc_financials/2026/ar/Amazon-2025-Annual-Report.pdf', 'data/corporate_filings/amazon_2025_annual_report.pdf' ),
]

for url, output in FILES:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size > 10000:
        print(f'Already present: {path}')
        continue
    print(f'Downloading: {path}')
    response = requests.get(url, headers={'User-Agent': 'ProofLoop/1.0'}, timeout=120)
    response.raise_for_status()
    path.write_bytes(response.content)
    print(f'Saved {path} ({path.stat().st_size} bytes)')

print('Deployment corpus download complete.')
