# EACLD-E0 — Raport de implementare și rezultate computaționale

**Data:** 4 noiembrie 2026. **Stadiu:** simulare executată, cod și rezultate reproductibile.

## 1. Obiectul experimentului

Se evaluează un algoritm de diagnostic diferențial activ pentru patru cauze: 
H1 — variație fizică a temperaturii; H2 — bias al traductorului; H3 — modificarea unui mesaj după autentificarea la sursă; H4 — retransmiterea unui mesaj autentic vechi.

Modelul include patru probe: citire fizică independentă (`reference_read`), provocare cu citire curentă a nodului (`node_challenge`), verificarea autentificatorului (`message_verify`) și verificarea secvenței (`sequence_check`).

Fiecare bloc experimental conține cele patru cauze cu **exact aceeași traiectorie P0** a temperaturii recepționate. Observațiile de securitate P1 sunt disponibile în funcție de politica de monitorizare pasivă. Pentru fiecare politică de diagnostic sunt utilizate aceleași rezultate potențiale ale probelor, cu acces numai la cele executate efectiv.

## 2. Model algoritmic și statistic

Modelul EACLD are opt stări latente, formate din patru ipoteze cauzale și două stări ale verificatorului comun (sănătos/defect). Inferența menține distribuția comună `P(H,C | D)`. Rezultatele verificărilor de integritate și secvență pot fi corelate marginal prin starea latentă comună `C`. B5 utilizează în schimb o factorizare care integrează `C` separat pentru fiecare observație.

Selecția B6 și B5 utilizează programare dinamică finită pe cele patru verificări admisibile. Ecuația Bellman este:

`V(b,S) = min { R(b), min_{a in S} [ c(a) + sum_z P(z|b,a) V(b_az,S minus {a}) ] }`.

Riscul terminal este `R(b) = min_d E[L(d,H)|b]`. Deciziile admise sunt cele patru cauze exacte, două clase agregate H1/H2 și H3/H4, respectiv verdictul nerezolvat. Matricea de pierdere diferențiază omisiunea unui atac, alarma falsă, confuzia între cauze și păstrarea unui verdict parțial. Costul probelor este scalar, în unități normalizate; latențele și traficul sunt metrici suplimentare, nu costuri monetare.

## 3. Protocolul de calibrare și evaluare

- **Calibrare:** 80 blocuri/mod de rețea, în total 640 episoade. Parametrii observațiilor sunt estimați exclusiv din această partiție, utilizând etichetele intervențiilor și starea verificatorului injectată.
- **Validare separată:** 20 blocuri/mod, în total 160 episoade; nu este folosită pentru ajustarea algoritmului.
- **Test:** 20 blocuri/mod, în total 160 episoade (4 cauze × 2 regimuri × 20 blocuri).
- **Estimare:** distribuții categoriale cu netezire Dirichlet, prior Beta pentru prevalența verificatorului defect; prior cauzal echilibrat.
- **Incertitudine:** 1.500 repetări bootstrap stratificat pe regimul de rețea, cu resampling la nivelul celor 40 de blocuri de test; comparațiile sunt pereche, toate politicile și cauzele rămân în același bloc.
- **Separarea informațiilor:** fișierele publice includ numai telemetria și rezultatele pasive; etichetele `H` și `C` și rezultatele potențiale ale verificărilor sunt ținute separat. Identificatorii publici nu codifică etichetele cauzale.

## 4. Politicile comparate

| Cod | Politică |
|---|---|
| B0 | Numai telemetrie P0, posterior prior echilibrat |
| B1 | Numai telemetrie P1, cu verificări de securitate deja existente |
| B2 | Execuția tuturor verificărilor neacoperite de P1 |
| B3 | Selecție aleatorie secvențială, cu același buget și prag de risc |
| B4 | Selecție greedy după câștig informațional raportat la cost |
| B5 | Planificare Bayes completă, dar cu dovezi tratate marginal ca independente |
| B6 | EACLD: planificare Bayes completă și model explicit al verificatorului comun |

**Definiții ale indicatorilor.** Macro-F1 se calculează pentru atribuirea exactă H1–H4; verdictele agregate și nerezolvate nu sunt clasificate ca identificări exacte. „Acoperire exactă” este fracția verdictelor care atribuie o cauză individuală, indiferent dacă atribuirea este corectă; „pierdere” este media valorilor din matricea decizională declarată în configurație; „pierdere + cost” adaugă costul realizat al probelor. Scorul Brier este suma erorilor pătratice pe cele patru probabilități posterioare.

## 5. Experimentul principal E0

| Politică | Macro-F1 | Acoperire exactă | Pierdere | Pierdere + cost | Probe/episod | Cost/episod | Brier |
|---|---:|---:|---:|---:|---:|---:|---:|
| B0_passive_P0 | 0.0000 | 0.0000 | 0.4600 | 0.4600 | 0.000 | 0.0000 | 0.7500 |
| B1_passive_P1 | 0.1571 | 0.0938 | 0.4183 | 0.4183 | 0.000 | 0.0000 | 0.6623 |
| B2_exhaustive | 0.9062 | 0.8625 | 0.0685 | 0.2065 | 3.544 | 0.1380 | 0.1148 |
| B3_random | 0.9099 | 0.8688 | 0.0671 | 0.1874 | 3.087 | 0.1202 | 0.1145 |
| B4_entropy_greedy | 0.9031 | 0.8688 | 0.0765 | 0.1788 | 2.844 | 0.1023 | 0.1262 |
| B5_naive_independence | 0.9092 | 0.9250 | 0.0925 | 0.1595 | 2.181 | 0.0670 | 0.1418 |
| B6_EACLD | 0.8991 | 0.9187 | 0.1089 | 0.1769 | 2.200 | 0.0681 | 0.1573 |

**Comparații pereche cu EACLD (B6):**

| Comparație (B6 minus referință) | Indicator | Diferență | IC bootstrap 95% |
|---|---|---:|---:|
| B2_exhaustive | Macro-F1 | -0.0062 | [-0.0374; +0.0245] |
| B2_exhaustive | Pierdere + cost | -0.0305 | [-0.0705; +0.0167] |
| B2_exhaustive | Costul probelor | -0.0700 | [-0.0744; -0.0652] |
| B2_exhaustive | Brier | +0.0417 | [+0.0029; +0.0882] |
| B4_entropy_greedy | Macro-F1 | -0.0033 | [-0.0338; +0.0269] |
| B4_entropy_greedy | Pierdere + cost | -0.0025 | [-0.0396; +0.0414] |
| B4_entropy_greedy | Costul probelor | -0.0343 | [-0.0375; -0.0310] |
| B4_entropy_greedy | Brier | +0.0307 | [-0.0014; +0.0691] |
| B5_naive_independence | Macro-F1 | -0.0101 | [-0.0267; +0.0000] |
| B5_naive_independence | Pierdere + cost | +0.0171 | [+0.0001; +0.0499] |
| B5_naive_independence | Costul probelor | +0.0011 | [+0.0000; +0.0026] |
| B5_naive_independence | Brier | +0.0152 | [-0.0004; +0.0413] |

## 6. Sensibilitate: exclusiv prevalenta verificatorului defect

| Politică | Macro-F1 | Acoperire exactă | Pierdere | Pierdere + cost | Probe/episod | Cost/episod | Brier |
|---|---:|---:|---:|---:|---:|---:|---:|
| B0_passive_P0 | 0.0000 | 0.0000 | 0.4600 | 0.4600 | 0.000 | 0.0000 | 0.7500 |
| B1_passive_P1 | 0.1377 | 0.0875 | 0.4291 | 0.4291 | 0.000 | 0.0000 | 0.6844 |
| B2_exhaustive | 0.8035 | 0.7500 | 0.1417 | 0.2799 | 3.556 | 0.1382 | 0.2143 |
| B3_random | 0.8035 | 0.7500 | 0.1417 | 0.2708 | 3.312 | 0.1291 | 0.2142 |
| B4_entropy_greedy | 0.8035 | 0.7500 | 0.1417 | 0.2620 | 3.188 | 0.1203 | 0.2141 |
| B5_naive_independence | 0.7992 | 0.7750 | 0.1613 | 0.2545 | 2.569 | 0.0932 | 0.2557 |
| B6_EACLD | 0.7970 | 0.7625 | 0.1592 | 0.2501 | 2.431 | 0.0909 | 0.2539 |

**Comparații pereche cu EACLD (B6):**

| Comparație (B6 minus referință) | Indicator | Diferență | IC bootstrap 95% |
|---|---|---:|---:|
| B2_exhaustive | Macro-F1 | -0.0064 | [-0.0310; +0.0158] |
| B2_exhaustive | Pierdere + cost | -0.0301 | [-0.0526; -0.0037] |
| B2_exhaustive | Costul probelor | -0.0474 | [-0.0516; -0.0431] |
| B2_exhaustive | Brier | +0.0393 | [+0.0072; +0.0766] |
| B4_entropy_greedy | Macro-F1 | -0.0064 | [-0.0310; +0.0158] |
| B4_entropy_greedy | Pierdere + cost | -0.0123 | [-0.0330; +0.0130] |
| B4_entropy_greedy | Costul probelor | -0.0295 | [-0.0331; -0.0258] |
| B4_entropy_greedy | Brier | +0.0395 | [+0.0074; +0.0769] |
| B5_naive_independence | Macro-F1 | -0.0021 | [-0.0209; +0.0160] |
| B5_naive_independence | Pierdere + cost | -0.0044 | [-0.0212; +0.0096] |
| B5_naive_independence | Costul probelor | -0.0023 | [-0.0040; -0.0006] |
| B5_naive_independence | Brier | -0.0019 | [-0.0216; +0.0145] |

## 7. Stres compus: verificator defect si observabilitate pasiva crescuta

| Politică | Macro-F1 | Acoperire exactă | Pierdere | Pierdere + cost | Probe/episod | Cost/episod | Brier |
|---|---:|---:|---:|---:|---:|---:|---:|
| B0_passive_P0 | 0.0000 | 0.0000 | 0.4600 | 0.4600 | 0.000 | 0.0000 | 0.7500 |
| B1_passive_P1 | 0.2476 | 0.1812 | 0.3954 | 0.3954 | 0.000 | 0.0000 | 0.6152 |
| B2_exhaustive | 0.8270 | 0.7875 | 0.1339 | 0.2654 | 3.169 | 0.1315 | 0.2193 |
| B3_random | 0.8312 | 0.7937 | 0.1325 | 0.2576 | 2.962 | 0.1251 | 0.2168 |
| B4_entropy_greedy | 0.8353 | 0.8000 | 0.1311 | 0.2491 | 2.806 | 0.1179 | 0.2134 |
| B5_naive_independence | 0.8327 | 0.8187 | 0.1452 | 0.2471 | 2.388 | 0.1019 | 0.2182 |
| B6_EACLD | 0.8375 | 0.7812 | 0.1155 | 0.2147 | 2.150 | 0.0992 | 0.1910 |

**Comparații pereche cu EACLD (B6):**

| Comparație (B6 minus referință) | Indicator | Diferență | IC bootstrap 95% |
|---|---|---:|---:|
| B2_exhaustive | Macro-F1 | +0.0106 | [-0.0034; +0.0270] |
| B2_exhaustive | Pierdere + cost | -0.0508 | [-0.0810; -0.0303] |
| B2_exhaustive | Costul probelor | -0.0323 | [-0.0355; -0.0287] |
| B2_exhaustive | Brier | -0.0281 | [-0.0563; -0.0037] |
| B4_entropy_greedy | Macro-F1 | +0.0023 | [-0.0084; +0.0119] |
| B4_entropy_greedy | Pierdere + cost | -0.0345 | [-0.0653; -0.0134] |
| B4_entropy_greedy | Costul probelor | -0.0187 | [-0.0222; -0.0153] |
| B4_entropy_greedy | Brier | -0.0223 | [-0.0494; +0.0024] |
| B5_naive_independence | Macro-F1 | +0.0047 | [-0.0146; +0.0241] |
| B5_naive_independence | Pierdere + cost | -0.0324 | [-0.0757; +0.0010] |
| B5_naive_independence | Costul probelor | -0.0027 | [-0.0060; +0.0003] |
| B5_naive_independence | Brier | -0.0273 | [-0.0623; +0.0029] |

## 8. Interpretarea rezultatelor

În experimentul principal, EACLD (B6) obține macro-F1 0,8991 și execută în medie 2,200 probe/episod, față de macro-F1 0,9062 și 3,544 probe/episod pentru verificarea exhaustivă B2. Costul mediu normalizat al probelor scade de la 0,1380 la 0,0681, adică aproximativ 50,7%. Diferența de macro-F1 are un interval bootstrap care include zero; și diferența de pierdere plus cost față de B2 include zero.

Varianta B5, care simplifică dependențele dintre sursele de dovezi, are în experimentul principal un scor agregat pierdere + cost mai mic decât B6 (0,1595 față de 0,1769). Acesta este un rezultat advers ipotezei că modelarea explicită a dependențelor aduce un avantaj în orice regim. Valoarea modelului complet trebuie studiată separat în funcție de frecvența defecțiunilor comune, precizia estimării distribuțiilor rare și gradul observabilității pasive.

Testul în care **numai prevalența** verificatorului defect este crescută la 0,24/0,45 produce B6: 0,2501 și B5: 0,2545 pentru pierdere + cost. Diferența este mică, iar intervalul bootstrap include zero. În testul de stres combinat, care crește concomitent prevalența, modifică severitatea eșecurilor și crește acoperirea verificărilor pasive, B6 produce pierdere + cost 0,2147 față de 0,2471 pentru B5. Acest ultim test măsoară un **regim compus** și nu izolează efectul unei singure variabile.

Aceste rezultate definesc o primă analiză comparativă a modelului. Avantajul robust care apare în toate cele trei configurații este reducerea volumului de verificări alese de EACLD față de politica exhaustivă. Efectul tratării explicite a surselor corelate variază cu regimul experimental și necesită o investigație dedicată a calibrării.

## 9. Caracterul rezultatelor și limitele modelului executat

Indicatorii din acest raport provin dintr-un simulator stochastic cu distribuții declarate și din modele probabilistice calibrate pe datele generate. **Nu provin din încercări pe ESP32, gateway-uri, senzori PT100, trafic MQTT real sau microservicii reale.** Latența și traficul sunt modelate numeric și se vor confrunta ulterior cu execuții fizice. Fiecare probă are un rezultat potențial pre-generat; modelul E0 presupune un episod suficient de staționar încât ordinea probelor să nu modifice rezultatul lor condiționat de cauza și starea verificatorului.

Programarea dinamică este exactă pentru cele patru probe E0. Extinderea la un număr mare de acțiuni necesită o formă de căutare limitată sau de optimizare aproximativă. Calibrarea modelului comun utilizează în această etapă etichetele stărilor injectate în antrenare; implementarea pe infrastructură reală va necesita definirea unui protocol de colectare și verificare a acestor etichete.

## 10. Inventarul artefactelor

- `eacld/core.py`: modelul formal discret, matricea de pierdere, inferența Bayesiană și programarea dinamică.
- `eacld/simulator.py`: injecția celor patru cauze, probele potențiale, eșecul verificatorului comun și calibrarea pe antrenare.
- `eacld/evaluation.py`: indicatorii, matricea confuziilor, evaluarea pe blocuri și bootstrap pereche stratificat.
- `run_experiment.py`: orchestrarea completă și exportul rezultatelor și figurilor.
- `config/`: configurația principală și cele două scenarii de sensibilitate.
- `data/public/`: date disponibile algoritmilor; `data/private/`: etichete cauzale și rezultate potențiale pentru evaluare.
- `results/test_decision_traces.jsonl`: deciziile, posteriorii, utilitățile probelor și motivele opririi pentru fiecare politică.
- `results/test_paired_bootstrap_95ci.csv`: diferențele B6–referință și intervalele bootstrap.
- `figures/`: graficele de performanță, cost, risc–acoperire, confuzie, frecvența probelor și calibrare.
- `tests/test_core.py`: teste pentru generare, identificabilitate, normalizarea probabilităților, independența etichetelor și complementaritatea probelor.

## 11. Reproducerea experimentului

```bash
python -m pip install -r requirements.txt
python -m pytest -q tests
python run_experiment.py --config config/e0_config.json --out .
python run_experiment.py --config config/e0_stress_verifier_only.json --out sensitivity/verifier_prevalence_only
python run_experiment.py --config config/e0_stress_config.json --out sensitivity/shared_verifier_stress
python make_report.py
```

Valorile aleatoare sunt determinate prin seed-uri fixe; alegerea aleatoare a probelor în B3 folosește seed derivat stabil din identificatorul episodului și numele politicii. Nu este utilizată informația despre cauza reală în interfața de execuție a unei politici.
