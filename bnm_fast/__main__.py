import bnm_fast.download
import bnm_fast.data
import asyncio

if __name__ == "__main__":
    asyncio.run(bnm_fast.download.main())
    bnm_fast.data.main()
