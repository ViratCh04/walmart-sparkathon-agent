from openai import OpenAI

client = OpenAI()

response = client.chat.completions.create(

    model="gpt-4o-mini-2024-07-18",

    messages=[

    {"role": "system", "content": "You are a fitness coach. Provide personalized workout advice."},

    {"role": "user", "content": "I want to build muscle but I only have 30 minutes a day to workout. What should I focus on?"}

    ]

)

print(response.choices[0].message.content)
