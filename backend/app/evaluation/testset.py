# # """
# # Module 10a — Evaluation Test Set
# # Small, hand-picked question/ground_truth pairs against the Apple 10-K,
# # covering both easily-answerable and known-hard cases (mirroring the
# # two contrasting scenarios already validated in Modules 7-8).
# # """

# # TESTSET = [
# #     {
# #         "question": "What are Apple's main risk factors related to product transitions?",
# #         "ground_truth": (
# #             "Apple faces risks from operating in highly volatile and competitive markets, "
# #             "requiring continual introduction of new products, services, and technologies, "
# #             "enhancement of existing offerings, stimulation of customer demand, and "
# #             "navigation of global regulatory requirements and market access barriers."
# #         ),
# #     },
# #     {
# #         "question": "What tax-related risks does Apple disclose?",
# #         "ground_truth": (
# #             "Apple is subject to examination of its tax returns by the IRS and other tax "
# #             "authorities. If effective tax rates increase or tax determinations exceed "
# #             "amounts previously accrued, it could materially affect the business, results "
# #             "of operations, financial condition, and stock price."
# #         ),
# #     },
# #     {
# #         "question": "What was Apple's exact stock buyback amount in Q3 2019?",
# #         "ground_truth": (
# #             "This information is not contained in Apple's FY2025 10-K filing, which does "
# #             "not report Q3 2019 figures."
# #         ),
# #     },
# # ]
# """
# Evaluation questions for the Apple 2025 Form 10-K.

# RAGAS quality metrics use only answerable questions. Unsupported questions
# are evaluated separately for safe refusal behavior because they should not be
# included in answer-quality averages.
# """

# ANSWERABLE_TESTSET = [
#     {
#         "question": "What are Apple's main risk factors related to product transitions?",
#         "ground_truth": (
#             "Apple faces risks from operating in highly volatile and competitive markets, "
#             "requiring continual introduction of new products, services, and technologies, "
#             "enhancement of existing offerings, stimulation of customer demand, and "
#             "navigation of global regulatory requirements and market access barriers."
#         ),
#     },
#     {
#         "question": "What tax-related risks does Apple disclose?",
#         "ground_truth": (
#             "Apple is subject to examination of its tax returns by the IRS and other tax "
#             "authorities. If effective tax rates increase or tax determinations exceed "
#             "amounts previously accrued, it could materially affect the business, results "
#             "of operations, financial condition, and stock price."
#         ),
#     },
# ]

# UNSUPPORTED_TESTSET = [
#     {
#         "question": "What was Apple's exact stock buyback amount in Q3 2019?",
#         "expected_behavior": "refuse_not_in_documents",
#     },
# ]

# # Keep this alias so existing imports continue to work. RAGAS will now receive
# # only answerable questions.
# TESTSET = ANSWERABLE_TESTSET
"""Evaluation data for the Apple 2025 Form 10-K."""

ANSWERABLE_TESTSET = [
    {
        "question": "What are Apple's main risk factors related to product transitions?",
        "ground_truth": (
            "Apple faces risks from operating in highly volatile and competitive markets, "
            "requiring continual introduction of new products, services, and technologies, "
            "enhancement of existing offerings, stimulation of customer demand, and "
            "navigation of global regulatory requirements and market access barriers."
        ),
    },
    {
        "question": "What tax-related risks does Apple disclose?",
        "ground_truth": (
            "Apple is subject to examination of its tax returns by the IRS and other tax "
            "authorities. If effective tax rates increase or tax determinations exceed "
            "amounts previously accrued, it could materially affect the business, results "
            "of operations, financial condition, and stock price."
        ),
    },
    {
        "question": "What risks does Apple disclose regarding its supply chain?",
        "ground_truth": (
            "Apple depends on third-party suppliers and manufacturing partners, and supply "
            "chain disruptions, component shortages, natural disasters, geopolitical events, "
            "or other disruptions could adversely affect its business and results."
        ),
    },
    {
        "question": "How does Apple describe competition in its markets?",
        "ground_truth": (
            "Apple operates in highly competitive markets and faces competition from companies "
            "with substantial resources, which can affect market share, pricing, innovation, "
            "and demand for its products and services."
        ),
    },
    {
        "question": "What regulatory risks does Apple identify?",
        "ground_truth": (
            "Apple faces risks from changing laws, regulations, government investigations, "
            "trade restrictions, privacy requirements, antitrust scrutiny, and rules affecting "
            "its products, services, platforms, and international operations."
        ),
    },
    {
        "question": "What does Apple disclose about foreign currency risk?",
        "ground_truth": (
            "Changes in foreign currency exchange rates can affect Apple's international "
            "revenue, expenses, margins, reported results, and financial condition."
        ),
    },
    {
        "question": "What risks are associated with Apple's dependence on intellectual property?",
        "ground_truth": (
            "Apple relies on intellectual property rights and may face claims of infringement, "
            "difficulty protecting its rights, litigation costs, or restrictions on its ability "
            "to use technology and content."
        ),
    },
    {
        "question": "What cybersecurity risks does Apple disclose?",
        "ground_truth": (
            "Cybersecurity incidents, unauthorized access, data loss, system disruptions, or "
            "attacks on Apple or its suppliers could harm operations, reputation, and financial results."
        ),
    },
]

UNSUPPORTED_TESTSET = [
    {
        "question": "What was Apple's exact stock buyback amount in Q3 2019?",
        "expected_behavior": "refuse_not_in_documents",
    },
    {
        "question": "What was Apple's revenue in fiscal year 2012?",
        "expected_behavior": "refuse_not_in_documents",
    },
]

# Existing RAGAS code can continue importing TESTSET.
TESTSET = ANSWERABLE_TESTSET