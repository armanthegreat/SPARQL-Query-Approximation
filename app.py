from appiepy import Product
import json


product = Product('https://www.ah.nl/producten/product/wi177754/ah-blauwe-bessen')



print(json.dumps(product.__dict__, indent=4, sort_keys=True))