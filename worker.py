import asyncio

import mistralai.workflows as workflows

from workflows.xelsius_agents import XelsiusAgentWorkflow


async def main():
    await workflows.run_worker([XelsiusAgentWorkflow])


if __name__ == "__main__":
    asyncio.run(main())
