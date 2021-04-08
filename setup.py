from distutils.core import setup
setup(
  name = 'Python_Brokers_API',         
  packages = ['Python_Brokers_API'],   
  version = '0.2',      
  license='MIT',        
  description = 'A package to make requests to brokers like binance,kraken',   
  author = 'Hugo Demenez',                  
  author_email = 'hdemenez@hotmail.fr',     
  url = 'https://github.com/hugodemenez/Python_Brokers_API',   
  download_url = 'https://github.com/hugodemenez/Python_Brokers_API/archive/refs/tags/v0.2.tar.gz', 
  keywords = ['Python', 'Brokers', 'API'],   
  install_requires=[           
          'time',
          'json',
          'hmac',
          'hashlib',
          'requests',
          'krakenex',
          'urllib',
      ],
  classifiers=[
    'Development Status :: 3 - Alpha',     
    'Intended Audience :: Developers',     
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: MIT License',  
    'Programming Language :: Python :: 3.9',    
  ],
)