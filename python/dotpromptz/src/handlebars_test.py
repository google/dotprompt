# import json as json_lib
# from typing import Any, Dict
# import handlebars
# # Try different initialization methods
# try:
#     # Method 1
#     hb = handlebars.Handlebars
# except:
#     try:
#         # Method 2
#         hb = handlebars.Handlebars.create()
#     except:
#         # Method 3
#         hb = handlebars
# # Print what we got to understand the structure
# print("Handlebars type:", type(handlebars))
# print("Available attributes:", dir(handlebars))

import handlebars

# Print what we're working with
print('Handlebars version:', handlebars.__file__)
print('Available attributes:', dir(handlebars))
