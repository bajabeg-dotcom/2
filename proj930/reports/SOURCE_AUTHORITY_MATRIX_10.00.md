# SOURCE AUTHORITY MATRIX 10.00

Verzija: 10.00.0-KOREKCIJA-BAZDARENJE-KALIBRACIJA
Datum: 2026-09-06T17:28:26.730802

## Autoriteti

- **FACTORY** = VELOCITY / DYNAMICS / RANGE REFERENCE (KOLIKO JAKO)
- **GOLD** = PLAYING LOGIC REFERENCE (KAKO SE SVIRA)
- **ENGINE** = INTELLIGENCE / TRANSFORMATION
- **KORG** = FINAL CONSTRAINT
- **VALIDATION** = AUTHORITY
- **LISTENING** = FINAL MUSICAL TRUTH

## Matrica

| PARAMETAR | FACTORY | GOLD | ENGINE |
|---|---|---|---|
| Velocity baseline | PRIMARY | SECONDARY | APPLY |
| Velocity curve | PRIMARY | VALIDATION | APPLY |
| Velocity range | PRIMARY | VALIDATION | APPLY |
| Dynamics | PRIMARY | SECONDARY | APPLY |
| Timing | SECONDARY | PRIMARY | APPLY |
| Microtiming | SECONDARY | PRIMARY | APPLY |
| Groove | SECONDARY | PRIMARY | APPLY |
| Trills | NO | PRIMARY | APPLY |
| Rolls | NO | PRIMARY | APPLY |
| Ornamentation | NO | PRIMARY | APPLY |
| Expression | SECONDARY | PRIMARY | APPLY |
| Articulation | REFERENCE | PRIMARY | APPLY |
| Phrase logic | REFERENCE | PRIMARY | APPLY |
| Humanization | NO | PRIMARY | APPLY |
| Arrangement behaviour | REFERENCE | PRIMARY | APPLY |
| Korg constraints | PRIMARY | PRIMARY | APPLY |
| Note range | PRIMARY | REFERENCE | APPLY |
| CC7 Mix | PRIMARY | NO | APPLY |
| CC11 Expression | REFERENCE | PRIMARY | APPLY |

## Conflict Resolution

**GOLD SHAPE + FACTORY RANGE + ENGINE CONSTRAINT**

Factory kaže: velocity = 72-98
Gold kaže: phrase behaviour = soft -> loud -> soft
Final: Gold određuje dynamics shape, Factory određuje legal velocity envelope

## Policy

NIKADA ne dozvoliti da slučajna funkcija promijeni source authority.