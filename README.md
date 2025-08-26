# SOK-Tim-9

Članovi tima:  
Petar Dragičević SV12/2022  
Luka Vuković SV37/2022  
Neven Ilinčić SV47/2022  
Mladen Petrić SV68/2022  
Dragan Jordanović SV79/2022  


# Uputstvo za instalaciju komponenti i parametrizaciju projekta u VS-codu

1. Instalirajte biblioteku za virtuelno okruženje: pip install virtenv
2. Pozicionirajte se u GraphVisualizer folder: cd GraphVisualizer
3. Kreirajte virtuelno okruženje: virtualenv *naziv_okruženja*
4. Aktivirajte virtuelno okruženje:
   <ol>
     <li>WINDOWS: *naziv_okruženja*/Scripts/activate </li>
     <li>LINUX: *naziv_okruženja*/bin/activate</li>
   </ol>
6. Instalirajte potrebne biblioteke koje se nalaze u requirements.txt: pip install -r requirements.txt 
7. Pozicionirajte se u graph_explorer folder: cd graph_explorer
8. Pokrenite aplikaciju: python manage.py runserver
9. U browser-u otvorite ip adresu koja vam je poslata u terminalu ukoliko je sve urađeno kako treba
