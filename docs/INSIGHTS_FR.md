# Ce que montre le premier essai

Résultats mesurés sur 64 références M5 du magasin CA_1, 84 jours de test et 20 simulations de délais. Les ventes sont réelles ; stocks initiaux, capacités, délais et coûts sont des hypothèses. Les fichiers agrégés et le manifeste figurent dans `docs/results`.

| Politique | Coût simulé moyen | Unités demandées servies |
|---|---:|---:|
| Moyenne saisonnière | 7 344,18 $ | 81,95 % |
| Saisonnière avec sécurité | 5 403,47 $ | 92,15 % |
| Moyenne ML | 6 787,24 $ | 84,00 % |
| ML avec sécurité | 5 039,95 $ | 94,34 % |

**1. L'incertitude change la décision.** Le modèle moyen seul laisse davantage de ventes non servies. À pénalité de rupture égale à 5 $ par unité, le stock de sécurité ML réduit le coût de 25,7 % par rapport à la politique utilisant la moyenne ML. Il augmente cependant le coût de détention : 2 268 $ contre 1 178 $.

**2. Le comparatif pertinent inclut une bonne référence simple.** Le ML avec sécurité coûte 6,7 % de moins que la saisonnalité avec sécurité et sert 2,18 points de demande supplémentaires dans cet essai. Ce résultat ne prouve pas une supériorité sur d'autres magasins, saisons ou paramètres.

**3. La meilleure politique dépend du coût métier.** À 2 $ par unité perdue, la politique moyenne ML a le coût ponctuel le plus bas : environ 4 057 $, contre 4 074 $ pour ML avec sécurité. L'écart est faible et n'établit pas une supériorité robuste. À 5 $, le classement change nettement. La sensibilité recalcule les coûts de politiques fixes ; elle ne réoptimise pas leurs paramètres.

**4. Un intervalle doit être vérifié.** À 12 jours, l'intervalle nominal à 80 % couvre 82,5 % des observations pour le ML contre 67,6 % pour la référence saisonnière. Il est plus large : cette protection supplémentaire a un coût. La calibration temporelle ne garantit pas la couverture future.

## Portée de l'étude

Ce projet personnel étudie les décisions de réapprovisionnement à partir de ventes historiques Walmart. Les résultats sont conditionnels au magasin, à la période et aux hypothèses de simulation. Ils ne représentent pas des économies réalisées chez Walmart. La configuration Kaggle de 512 références définit une extension possible ; elle n'a pas été exécutée pour cet essai.
