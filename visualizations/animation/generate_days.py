from pathlib import Path

cleaned_dir = Path("output/geojson")
geojson_files = sorted(cleaned_dir.glob("*.geojson"))
days = [f.stem for f in geojson_files]

day_string = ','.join([f'"{day}"' for day in days if day != 'combined'])
print(f'const days = [{day_string}];')
