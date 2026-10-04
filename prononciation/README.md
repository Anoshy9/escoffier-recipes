# Say It British

Application pour téléphone Android qui analyse et corrige votre prononciation de l'anglais britannique.
Elle est pensée pour les francophones et cible les sons qui posent problème quand on parle français.

## Comment ça marche

1. Choisissez un son à travailler (TH, H aspiré, ship/sheep, -ed, R britannique…) ou tapez votre propre phrase.
2. Touchez **Écouter** (ou **Ralenti**) pour entendre une voix britannique. Touchez un mot pour l'entendre seul.
3. Touchez le **micro rouge** et lisez la phrase.
4. La reconnaissance vocale de Google, réglée sur l'anglais britannique (`en-GB`), joue le rôle d'un auditeur anglais :
   - un **score** indique quelle part de la phrase a été comprise ;
   - les mots mal compris sont soulignés en rouge, les mots non entendus sont barrés ;
   - pour chaque erreur, l'application devine le son en cause (« think » compris « sink » donne le conseil sur le TH)
     et explique en français comment placer la langue et les lèvres.
5. **M'enregistrer** vous permet de réécouter votre voix et de la comparer au modèle.

Les scores sont gardés sur le téléphone. Les phrases sous 70 % apparaissent dans **À revoir**.

## Installer sur Android

La reconnaissance vocale a besoin de **Google Chrome** et d'une connexion internet.
La page doit être servie en HTTPS pour que Chrome autorise le micro.

**Option 1 : GitHub Pages (gratuit)**

1. Sur GitHub, ouvrez le dépôt, puis **Settings → Pages**.
2. Dans *Build and deployment*, choisissez *Deploy from a branch*, sélectionnez la branche qui contient ce dossier et `/ (root)`, puis **Save**.
3. Après une minute, l'application est à l'adresse `https://<votre-compte>.github.io/<dépôt>/prononciation/`.

GitHub Pages sur un dépôt privé demande un compte payant. Sinon, utilisez l'option 2.

**Option 2 : Netlify Drop (gratuit, sans compte au départ)**

Glissez le dossier `prononciation` sur <https://app.netlify.com/drop>. Netlify donne une adresse HTTPS.

**Puis, sur le téléphone**

1. Ouvrez l'adresse dans Chrome.
2. Menu **⋮ → Ajouter à l'écran d'accueil** (ou **Installer l'application**).
3. Au premier appui sur le micro, autorisez l'accès au microphone.

Si aucune voix britannique ne sort : **Paramètres Android → Synthèse vocale → Moteur Google → Installer les données vocales → English (United Kingdom)**.

## Fichiers

| Fichier | Rôle |
| --- | --- |
| `index.html`, `style.css` | Interface |
| `app.js` | Leçons, écoute, micro, enregistrement, progression |
| `analyse.js` | Comparaison mot à mot et diagnostic du son en cause |
| `data.js` | Leçons, transcriptions phonétiques, conseils, paires minimales |
| `sw.js`, `manifest.webmanifest`, icônes | Installation sur l'écran d'accueil et fonctionnement hors ligne |
| `test_analyse.js` | Tests du moteur d'analyse : `node prononciation/test_analyse.js` |

## Limites

- L'application juge si vous êtes **compris**, pas si votre accent est parfait.
  Un mot bien reconnu peut encore sonner français ; utilisez l'enregistrement pour comparer.
- Le diagnostic du son en cause est une estimation à partir du mot compris à la place. Il est fiable sur les erreurs typiques
  (TH, H, voyelles courtes ou longues, -ed, consonnes finales), moins sur les mots longs.
- Pour ajouter des exercices, éditez `data.js`.
