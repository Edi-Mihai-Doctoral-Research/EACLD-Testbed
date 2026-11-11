"""Rebuild a Romanian-language research record from the exact saved CSV results."""
from pathlib import Path
import pandas as pd
import json

ROOT=Path(__file__).resolve().parent
CASES=[
  ('Experimentul principal E0',ROOT),
  ('Sensibilitate: exclusiv prevalenta verificatorului defect',ROOT/'sensitivity/verifier_prevalence_only'),
  ('Stres compus: verificator defect si observabilitate pasiva crescuta',ROOT/'sensitivity/shared_verifier_stress')
]
POLICIES=[
  'B0_passive_P0','B1_passive_P1','B2_exhaustive','B3_random',
  'B4_entropy_greedy','B5_naive_independence','B6_EACLD'
]


def report_table(df):
    cols=['policy','macro_f1','exact_coverage','mean_realized_loss','mean_loss_plus_probe_cost','mean_probes','mean_cost','mean_brier']
    head='| Politică | Macro-F1 | Acoperire exactă | Pierdere | Pierdere + cost | Probe/episod | Cost/episod | Brier |'
    out=[head,'|---|---:|---:|---:|---:|---:|---:|---:|']
    for policy in POLICIES:
        r=df[df.policy==policy].iloc[0]
        out.append(f"| {policy} | {r.macro_f1:.4f} | {r.exact_coverage:.4f} | {r.mean_realized_loss:.4f} | "
                   f"{r.mean_loss_plus_probe_cost:.4f} | {r.mean_probes:.3f} | {r.mean_cost:.4f} | {r.mean_brier:.4f} |")
    return '\n'.join(out)


def ci_table(df):
    lines=['| Comparație (B6 minus referință) | Indicator | Diferență | IC bootstrap 95% |',
           '|---|---|---:|---:|']
    pairs=['B2_exhaustive','B4_entropy_greedy','B5_naive_independence']
    for compare in pairs:
        for metric,display in [
          ('macro_f1','Macro-F1'),('mean_loss_plus_probe_cost','Pierdere + cost'),
          ('mean_cost','Costul probelor'),('mean_brier','Brier')]:
            r=df[(df.comparison==f'B6_EACLD_minus_{compare}')&(df.metric==metric)].iloc[0]
            lines.append(f"| {compare} | {display} | {r.estimate:+.4f} | [{r.ci_low_95:+.4f}; {r.ci_high_95:+.4f}] |")
    return '\n'.join(lines)

config=json.loads((ROOT/'config/e0_config.json').read_text())
lines=['# EACLD-E0 — Raport de implementare și rezultate computaționale',
       '', '**Data:** 4 noiembrie 2026. **Stadiu:** simulare executată, cod și rezultate reproductibile.',
       '', '## 1. Obiectul experimentului',
       '', 'Se evaluează un algoritm de diagnostic diferențial activ pentru patru cauze: ',
       'H1 — variație fizică a temperaturii; H2 — bias al traductorului; H3 — modificarea unui mesaj după autentificarea la sursă; H4 — retransmiterea unui mesaj autentic vechi.',
       '', 'Modelul include patru probe: citire fizică independentă (`reference_read`), provocare cu citire curentă a nodului (`node_challenge`), verificarea autentificatorului (`message_verify`) și verificarea secvenței (`sequence_check`).',
       '', 'Fiecare bloc experimental conține cele patru cauze cu **exact aceeași traiectorie P0** a temperaturii recepționate. Observațiile de securitate P1 sunt disponibile în funcție de politica de monitorizare pasivă. Pentru fiecare politică de diagnostic sunt utilizate aceleași rezultate potențiale ale probelor, cu acces numai la cele executate efectiv.',
       '', '## 2. Model algoritmic și statistic',
       '', 'Modelul EACLD are opt stări latente, formate din patru ipoteze cauzale și două stări ale verificatorului comun (sănătos/defect). Inferența menține distribuția comună `P(H,C | D)`. Rezultatele verificărilor de integritate și secvență pot fi corelate marginal prin starea latentă comună `C`. B5 utilizează în schimb o factorizare care integrează `C` separat pentru fiecare observație.',
       '', 'Selecția B6 și B5 utilizează programare dinamică finită pe cele patru verificări admisibile. Ecuația Bellman este:',
       '', '`V(b,S) = min { R(b), min_{a in S} [ c(a) + sum_z P(z|b,a) V(b_az,S minus {a}) ] }`.',
       '', 'Riscul terminal este `R(b) = min_d E[L(d,H)|b]`. Deciziile admise sunt cele patru cauze exacte, două clase agregate H1/H2 și H3/H4, respectiv verdictul nerezolvat. Matricea de pierdere diferențiază omisiunea unui atac, alarma falsă, confuzia între cauze și păstrarea unui verdict parțial. Costul probelor este scalar, în unități normalizate; latențele și traficul sunt metrici suplimentare, nu costuri monetare.',
       '', '## 3. Protocolul de calibrare și evaluare',
       '', f"- **Calibrare:** {config['blocks_per_mode']['train']} blocuri/mod de rețea, în total 640 episoade. Parametrii observațiilor sunt estimați exclusiv din această partiție, utilizând etichetele intervențiilor și starea verificatorului injectată.",
       f"- **Validare separată:** {config['blocks_per_mode']['validation']} blocuri/mod, în total 160 episoade; nu este folosită pentru ajustarea algoritmului.",
       f"- **Test:** {config['blocks_per_mode']['test']} blocuri/mod, în total 160 episoade (4 cauze × 2 regimuri × 20 blocuri).",
       '- **Estimare:** distribuții categoriale cu netezire Dirichlet, prior Beta pentru prevalența verificatorului defect; prior cauzal echilibrat.',
       '- **Incertitudine:** 1.500 repetări bootstrap stratificat pe regimul de rețea, cu resampling la nivelul celor 40 de blocuri de test; comparațiile sunt pereche, toate politicile și cauzele rămân în același bloc.',
       '- **Separarea informațiilor:** fișierele publice includ numai telemetria și rezultatele pasive; etichetele `H` și `C` și rezultatele potențiale ale verificărilor sunt ținute separat. Identificatorii publici nu codifică etichetele cauzale.',
       '', '## 4. Politicile comparate',
       '', '| Cod | Politică |', '|---|---|',
       '| B0 | Numai telemetrie P0, posterior prior echilibrat |',
       '| B1 | Numai telemetrie P1, cu verificări de securitate deja existente |',
       '| B2 | Execuția tuturor verificărilor neacoperite de P1 |',
       '| B3 | Selecție aleatorie secvențială, cu același buget și prag de risc |',
       '| B4 | Selecție greedy după câștig informațional raportat la cost |',
       '| B5 | Planificare Bayes completă, dar cu dovezi tratate marginal ca independente |',
       '| B6 | EACLD: planificare Bayes completă și model explicit al verificatorului comun |',
       '', '**Definiții ale indicatorilor.** Macro-F1 se calculează pentru atribuirea exactă H1–H4; verdictele agregate și nerezolvate nu sunt clasificate ca identificări exacte. „Acoperire exactă” este fracția verdictelor care atribuie o cauză individuală, indiferent dacă atribuirea este corectă; „pierdere” este media valorilor din matricea decizională declarată în configurație; „pierdere + cost” adaugă costul realizat al probelor. Scorul Brier este suma erorilor pătratice pe cele patru probabilități posterioare.',
       '']
for title,base in CASES:
    metrics=pd.read_csv(base/'results/test_summary.csv')
    cis=pd.read_csv(base/'results/test_paired_bootstrap_95ci.csv')
    lines += [f'## {5+CASES.index((title,base))}. {title}', '',report_table(metrics),'',
              '**Comparații pereche cu EACLD (B6):**','',ci_table(cis),'']
lines += [
'## 8. Interpretarea rezultatelor',
'',
'În experimentul principal, EACLD (B6) obține macro-F1 0,8991 și execută în medie 2,200 probe/episod, față de macro-F1 0,9062 și 3,544 probe/episod pentru verificarea exhaustivă B2. Costul mediu normalizat al probelor scade de la 0,1380 la 0,0681, adică aproximativ 50,7%. Diferența de macro-F1 are un interval bootstrap care include zero; și diferența de pierdere plus cost față de B2 include zero.',
'',
'Varianta B5, care simplifică dependențele dintre sursele de dovezi, are în experimentul principal un scor agregat pierdere + cost mai mic decât B6 (0,1595 față de 0,1769). Acesta este un rezultat advers ipotezei că modelarea explicită a dependențelor aduce un avantaj în orice regim. Valoarea modelului complet trebuie studiată separat în funcție de frecvența defecțiunilor comune, precizia estimării distribuțiilor rare și gradul observabilității pasive.',
'',
'Testul în care **numai prevalența** verificatorului defect este crescută la 0,24/0,45 produce B6: 0,2501 și B5: 0,2545 pentru pierdere + cost. Diferența este mică, iar intervalul bootstrap include zero. În testul de stres combinat, care crește concomitent prevalența, modifică severitatea eșecurilor și crește acoperirea verificărilor pasive, B6 produce pierdere + cost 0,2147 față de 0,2471 pentru B5. Acest ultim test măsoară un **regim compus** și nu izolează efectul unei singure variabile.',
'',
'Aceste rezultate definesc o primă analiză comparativă a modelului. Avantajul robust care apare în toate cele trei configurații este reducerea volumului de verificări alese de EACLD față de politica exhaustivă. Efectul tratării explicite a surselor corelate variază cu regimul experimental și necesită o investigație dedicată a calibrării.',
'',
'## 9. Caracterul rezultatelor și limitele modelului executat',
'',
'Indicatorii din acest raport provin dintr-un simulator stochastic cu distribuții declarate și din modele probabilistice calibrate pe datele generate. **Nu provin din încercări pe ESP32, gateway-uri, senzori PT100, trafic MQTT real sau microservicii reale.** Latența și traficul sunt modelate numeric și se vor confrunta ulterior cu execuții fizice. Fiecare probă are un rezultat potențial pre-generat; modelul E0 presupune un episod suficient de staționar încât ordinea probelor să nu modifice rezultatul lor condiționat de cauza și starea verificatorului.',
'',
'Programarea dinamică este exactă pentru cele patru probe E0. Extinderea la un număr mare de acțiuni necesită o formă de căutare limitată sau de optimizare aproximativă. Calibrarea modelului comun utilizează în această etapă etichetele stărilor injectate în antrenare; implementarea pe infrastructură reală va necesita definirea unui protocol de colectare și verificare a acestor etichete.',
'',
'## 10. Inventarul artefactelor',
'',
'- `eacld/core.py`: modelul formal discret, matricea de pierdere, inferența Bayesiană și programarea dinamică.',
'- `eacld/simulator.py`: injecția celor patru cauze, probele potențiale, eșecul verificatorului comun și calibrarea pe antrenare.',
'- `eacld/evaluation.py`: indicatorii, matricea confuziilor, evaluarea pe blocuri și bootstrap pereche stratificat.',
'- `run_experiment.py`: orchestrarea completă și exportul rezultatelor și figurilor.',
'- `config/`: configurația principală și cele două scenarii de sensibilitate.',
'- `data/public/`: date disponibile algoritmilor; `data/private/`: etichete cauzale și rezultate potențiale pentru evaluare.',
'- `results/test_decision_traces.jsonl`: deciziile, posteriorii, utilitățile probelor și motivele opririi pentru fiecare politică.',
'- `results/test_paired_bootstrap_95ci.csv`: diferențele B6–referință și intervalele bootstrap.',
'- `figures/`: graficele de performanță, cost, risc–acoperire, confuzie, frecvența probelor și calibrare.',
'- `tests/test_core.py`: teste pentru generare, identificabilitate, normalizarea probabilităților, independența etichetelor și complementaritatea probelor.',
'',
'## 11. Reproducerea experimentului',
'',
'```bash',
'python -m pip install -r requirements.txt',
'python -m pytest -q tests',
'python run_experiment.py --config config/e0_config.json --out .',
'python run_experiment.py --config config/e0_stress_verifier_only.json --out sensitivity/verifier_prevalence_only',
'python run_experiment.py --config config/e0_stress_config.json --out sensitivity/shared_verifier_stress',
'python make_report.py',
'```',
'',
'Valorile aleatoare sunt determinate prin seed-uri fixe; alegerea aleatoare a probelor în B3 folosește seed derivat stabil din identificatorul episodului și numele politicii. Nu este utilizată informația despre cauza reală în interfața de execuție a unei politici.',
]
(ROOT/'RAPORT_REZULTATE_E0.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('Wrote:',ROOT/'RAPORT_REZULTATE_E0.md')
