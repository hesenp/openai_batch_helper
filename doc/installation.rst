Installation
============

Requirements
------------

- Python 3.9+
- An OpenAI API key in ``OPENAI_API_KEY`` for live examples

From PyPI (future)
------------------

.. code-block:: bash

   pip install batch-helper

From source (development)
-------------------------

.. code-block:: bash

   git clone <repo-url>
   cd batch-helper
   pip install -e .[dev]

Quality checks
--------------

.. code-block:: bash

   pytest -q
   mypy batch_helper
   ruff check .

