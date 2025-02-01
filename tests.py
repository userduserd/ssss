import asyncio

import aiohttp

a = 535
async def get_req(kzt_amount):
    url = f"http://38.244.134.231:8000/req/"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={"amount": kzt_amount}) as res:
                print("Status:", res.status)  # Логирование статуса ответа
                if res.status == 200:
                    json_data = await res.json()
                    req = json_data.get("req")
                    uniq_invoice_id = json_data.get("invoice_id")
                    return req, uniq_invoice_id
                else:
                    error_data = await res.json()
                    return None
    except Exception as e:
        print("Exception:", e)
asyncio.run(get_req(10000))
