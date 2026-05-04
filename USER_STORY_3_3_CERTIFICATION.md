# Certification — User Story 3.3

## Backward Compatibility & API Bridging

**Date:** 2026-05-04  
**Status:** ✅ Certifié

---

## 1) Endpoints bridgés vers le moteur d’état

### Ponts d’écriture legacy
- `POST /students/summer-school/enroll`
  - Route legacy conservée
  - Appelle maintenant `StateEngine.apply_event(...)`
  - Synchronise : `SummerSchoolEnrollment` + `StudentState` + `StateTransitionLog`

- `DELETE /students/summer-school/{enrollment_id}`
  - Route legacy conservée
  - Appelle maintenant `StateEngine.apply_event(...)`
  - Synchronise : suppression de `SummerSchoolEnrollment` + mise à jour de `StudentState` + `StateTransitionLog`

### Pont de triage / résolution
- `POST /students/{fiche}/evaluation`
  - Point de compatibilité ajouté pour les actions de résolution manuelle
  - Utilise `MANUAL_VETTING` / `RESOLVE_REVIEW` via `StateEngine.apply_event(...)`
  - Préserve le contrat d’évaluation attendu par le frontend

### Endpoints GET de triage
- `GET /students/triage-matrix/{academic_year}/{level}`
- `GET /students/triage-drilldown/{academic_year}/{level}`

Ces endpoints restent **read-only** et n’ont pas besoin de pont d’écriture.

---

## 2) Validation d’audit

Les actions passées par l’ancienne UI produisent désormais des logs enrichis dans `StateTransitionLog` avec :
- `event_name`
- `from_state`
- `to_state`
- `to_workflow_state`
- `to_final_april_state`
- `reason_codes`
- métadonnées métier de synchronisation
- alias de compatibilité historique `legacy_summer_sync`

### Preuves validées par tests
- création / mise à jour de l’inscription d’été
- suppression de l’inscription d’été
- résolution manuelle via le pont d’évaluation
- audit log créé à chaque action significative
- cycle de vie complet Émile: héritage, garde IFP, pont legacy, audit explicite, clôture finale

---

## 3) Santé du système

### Résultats de tests
- Suite ciblée de pont API : **3/3 OK**
- Régression ciblée (`apply_event`, summer bridge, API bridge, re-assessment, grand cycle) : **25/25 OK**
- Suite complète `students` : **71/71 OK**

### Conclusion
- Aucun test historique cassé
- Aucun changement de contrat HTTP observé sur les routes legacy concernées
- Le moteur d’état est désormais l’unique point d’écriture métier pour ces flux

---

## 4) Conclusion de certification

**La compatibilité ascendante est maintenue, le pont API fonctionne, et l’audit est enrichi sans casser le frontend existant.**

**Statut final : ✅ prêt pour production**

