# Analyseur d'humeur

Petite application web qui regarde ton visage (webcam ou photo) et devine ton
humeur : **content, triste, surpris, en colère, apeuré, dégoûté ou neutre**.

Tout tourne dans le navigateur : aucune image ne quitte ton ordinateur.

## Lancer l'application

Le navigateur doit pouvoir charger les modèles d'IA depuis le dossier `modeles/`,
il faut donc passer par un petit serveur local (ouvrir `index.html` en
double-cliquant ne suffit pas toujours) :

```bash
cd analyseur_humeur
python3 -m http.server 8000
```

Puis ouvrir <http://localhost:8000> dans Chrome, Firefox, Edge ou Safari,
cliquer sur **Démarrer la caméra** et autoriser l'accès à la webcam.
On peut aussi cliquer sur **Prendre un selfie** (sur téléphone, cela ouvre
l'appareil photo) ou sur **Analyser une photo** pour choisir une image.

## Sur téléphone

Le navigateur n'autorise la webcam que sur une page en HTTPS (ou sur
`localhost`). Pour l'utiliser sur un téléphone, il faut donc héberger ce dossier
sur un site en HTTPS (par exemple GitHub Pages). Sinon, le bouton
**Prendre un selfie** fonctionne partout : il prend une photo et l'analyse.

## Ce que l'on voit

- un cadre autour de chaque visage, avec l'humeur détectée ;
- la grande émoji de l'humeur dominante et le niveau de confiance ;
- le pourcentage de chacune des 7 expressions ;
- une frise « humeur au fil du temps » sur les 30 dernières secondes.

Les résultats de la webcam sont moyennés sur quelques images pour éviter que
l'affichage ne saute d'une humeur à l'autre.

## Comment ça marche

- [face-api.js](https://github.com/vladmandic/face-api) (licence MIT, copie dans
  `lib/`) basé sur TensorFlow.js ;
- `modeles/tiny_face_detector_model` trouve les visages dans l'image ;
- `modeles/face_expression_model` estime la probabilité de chaque expression.

Les calculs utilisent la carte graphique (WebGL) quand c'est possible, sinon le
processeur.

## Limites

C'est une estimation à partir de l'expression du visage, pas une lecture des
émotions réelles. Les résultats sont meilleurs avec un visage bien éclairé, de
face, sans lunettes de soleil ni masque, et avec des expressions assez marquées.
