import ijson
import csv
import sys

def extract_steam_data(input_file, output_file):
    print(f"Reading {input_file} and extracting data...")

    columns_to_keep = [
        'name',
        'release_date',
        'price',
        'windows',
        'mac',
        'linux',
        'metacritic_score',
        'achievements',
        'categories',
        'genres',
        'user_score',
        'positive',
        'negative'
    ]

    count = 0
    try:
        with open(input_file, 'rb') as infile, open(output_file, 'w', newline='', encoding='utf-8') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=columns_to_keep)
            writer.writeheader()

            # The json is an object mapping IDs to game data.
            # ijson.kvitems(infile, '') yields (key, value) where key is game ID and value is the game dict.
            for game_id, game_data in ijson.kvitems(infile, ''):
                row = {}
                for col in columns_to_keep:
                    # handle missing values
                    val = game_data.get(col, None)
                    # convert lists to string representations for CSV
                    if isinstance(val, list):
                        val = ', '.join(map(str, val))
                    row[col] = val
                
                writer.writerow(row)
                count += 1
                
                if count % 10000 == 0:
                    print(f"Processed {count} records...")

        print(f"Successfully processed {count} records. Saved to {output_file}.")
    except Exception as e:
        print(f"Error processing file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    extract_steam_data('games.json', 'games_extracted.csv')
