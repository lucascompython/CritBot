import asyncpraw
import asyncio
import random






async def main():
    async with asyncpraw.Reddit(
        client_id="y8DZE9fKtd4TdtesNPLJAA",
        client_secret="U25KgvCiNwURg6Gknlzo2oQJTYEi_w",
        user_agent="CritBot"
    ) as reddit:
        reddit.read_only = True

        subreddit = await reddit.subreddit("memes")

        submissions = []
        async for submission in subreddit.top(limit=100, time_filter="week"):
            submissions.append(submission.title)

        random_choice = random.choice(submissions)        
        print(random_choice)


asyncio.run(main())