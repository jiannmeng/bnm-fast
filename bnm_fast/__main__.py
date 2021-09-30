import argparse
import asyncio

import bnm_fast.download
import bnm_fast.transform
from bnm_fast.common import logger

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--download", action="store_true")
    parser.add_argument("-t", "--transform", action="store_true")
    args = parser.parse_args()

    if not args.download and not args.transform:
        logger.info("Flags omitted, so all steps in the workflow will be run")
        args.download = True
        args.transform = True

    if args.download:
        logger.info("Running download step...")
        asyncio.run(bnm_fast.download.main())
    else:
        logger.info("Skipping download step")

    if args.transform:
        logger.info("Running transform step...")
        bnm_fast.transform.main()
    else:
        logger.info("Skipping transform step")

    logger.info("All steps completed")
