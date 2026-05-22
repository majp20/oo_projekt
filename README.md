## Projekt: Spremembe barvnih palet skozi čas

Projekt prikazuje, kako se barvne palete spreminjajo skozi umetnostna obdobja. Podatki se izračunajo iz lokalnih slik v mapi `images`, rezultat pa se zapiše v `art_periods_data.json`, ki ga nato prebere stran `OO_projekt.html`.

## Struktura projekta

```text
.
├── OO_projekt.html        # Interaktivni prikaz obdobij, del in barvnih palet
├── extract_colors.py      # Algoritem za branje slik in izračun barv
├── art_periods_data.json  # Generirani podatki za spletno stran
├── images/                # Lokalne slike umetniških del
└── README.md              # Opis projekta in algoritma
```

## Zagon

Najprej zaženi izračun barv:

```bash
python extract_colors.py
```

Za pravilen prikaz JSON podatkov odpri stran prek lokalnega strežnika:

```bash
python -m http.server 8080
```

Nato v brskalniku odpri:

```text
http://localhost:8080/OO_projekt.html
```

## Kaj projekt prikazuje

- 8 umetnostnih obdobij
- skupno paleto najbolj značilnih barv za vsako obdobje
- primere umetniških del za vsako obdobje
- ločeno barvno paleto pod vsakim posameznim delom
- interaktiven časovni trak za pregled obdobij

## Uporabljene knjižnice

Algoritem uporablja:

- `Pillow` za odpiranje slik, popravljanje EXIF orientacije in pretvorbo v RGB
- `NumPy` za hitro obdelavo pikslov in računanje barvnih skupin
- standardne Python knjižnice `json`, `pathlib`, `collections` in `re`

K-means se ne uporablja več, ker lahko centroidi ustvarijo barve, ki niso dejanski piksli slike.

## Algoritem

### 1. Branje slike

Skripta prebere vsako lokalno sliko iz mape `images`. Slika se pretvori v RGB, pri slikah s prosojnostjo pa se prosojni deli združijo z belo podlago.

Slike se ne pomanjšujejo z interpolacijo, ker bi interpolacija ustvarila nove barve. Pri zelo velikih slikah skripta vzame determinističen vzorec realnih pikslov, zato izračun ostane hiter, barve pa še vedno izvirajo iz dejanske slike.

### 2. Združevanje podobnih pikslov

Vsak piksel se pretvori v HSV prostor. Barve se nato združijo v majhne skupine:

- odtenek: približno 8 stopinj
- nasičenost: približno 8 %
- svetlost: približno 8 %

Nevtralnim barvam, kot so bela, siva in črna, se odtenek ne upošteva enako strogo, ker pri njih hue ni zanesljiv podatek.

### 3. Izbor izrazitih barv

Za vsako barvno skupino se izračuna:

- koliko pikslov zavzame v sliki
- kako nasičena je barva
- kako svetla je barva

Najpomembnejši je delež slike, nasičenost in svetlost pa pomagata, da se pomembni barvni poudarki ne izgubijo.

### 4. Samo realne barve

Končna HEX barva nikoli ni povprečje ali umetno ustvarjen odtenek. Za vsako izbrano skupino skripta poišče dejanski piksel iz slike, ki najbolje predstavlja to skupino, in iz tega piksla naredi HEX vrednost.

To pomeni, da se barve v paleti res pojavijo v sliki.

### 5. Brez podvojenih in napačnih barv

Pri posameznem umetniškem delu algoritem ne zapolnjuje palete na silo. Če slika nima šest dovolj različnih izrazitih barv, prikaže manj barv. To prepreči podvojene odtenke in barve, ki bi bile dodane samo zato, da bi bilo v paleti vedno šest polj.

Za obdobje se barve izračunajo iz združenih pikslov vseh del tega obdobja. Tako skupna paleta predstavlja barve, ki se v obdobju najpogosteje in najizraziteje pojavljajo.

### 6. Imena barv

Imena barv se izračunajo neposredno iz HEX vrednosti. Skripta pri tem uporabi svetlost, nasičenost in odtenek, zato se imena, kot so `Bela`, `Črna`, `Rjava`, `Rumena`, `Modra`, `Turkizna` ali `Rdeča`, ujemajo z dejansko HEX barvo.

## Prikaz na strani

`OO_projekt.html` bere podatke iz `art_periods_data.json`. Vsako delo uporablja svojo lastno paleto iz `dela[].paleta`; če ima delo manj kot šest pravilnih barv, se prikaže samo toliko barv. Paleta posameznega dela se ne nadomešča več s paleto celotnega obdobja.

