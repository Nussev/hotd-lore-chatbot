import orjson

# Path to your raw Reddit data file (JSON Lines format)
# Each line is a separate JSON object representing one past
file_path = "data_raw/r_HouseOfTheDragon_posts.jsonl"

# Counter to limit how many posts we print
count = 0

# Open the file in read mode
with open(file_path, "r", encoding="utf-8") as f:

    # Iterate over each line (each line = one Reddit post)
    for line in f:

        # Convert the JSON string into a Python dictionary
        # Example: '{"title": "...", "score": 123}' → dict
        post = orjson.loads(line)

        # Print the post title (main text field we care about distribution
        print("TITLE:", post.get("title"))

        # Print the score (upvotes) to understand quality distribution
        print("SCORE:", post.get("score"))

        # Separator so output is readable in terminal
        print("-" * 40)

        # Increment counter so we only inspect a small sample

        count += 1

        # Stop after 5 posts so we don't flood the terminal
        if count == 5:
            break

