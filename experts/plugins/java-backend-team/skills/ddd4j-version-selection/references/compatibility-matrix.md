# Compatibility Matrix

> Collection date: 2026-09-11. Re-read the current POMs, matrix scripts, and remote state before use.

## ddd4j

| Line | JDK | Maven/POM | revision |
|---|---:|---|---|
| 1.0.x | 8 | Maven 3 / 4.0.0 | 1.0.x.20260630-SNAPSHOT |
| 2.0.x | 17 | Maven 3 / 4.0.0 | 2.0.x.20260630-SNAPSHOT |
| 3.0.x | 21 | Maven 4 / 4.1.0 | 3.0.x.20260630-SNAPSHOT |

## ddd4j-boot

| Boot Line | Spring Boot | ddd4j | JDK | Maven/POM |
|---|---|---|---:|---|
| 2.3.x | 2.3.12.RELEASE | 1.0.x | 8 | Maven 3 / 4.0 |
| 2.4.x | 2.4.13 | 1.0.x | 8 | Maven 3 / 4.0 |
| 2.5.x | 2.5.15 | 1.0.x | 8 | Maven 3 / 4.0 |
| 2.6.x | 2.6.15 | 1.0.x | 8 | Maven 3 / 4.0 |
| 2.7.x | 2.7.18 | 1.0.x | 8 | Maven 3 / 4.0 |
| 3.0.x | 3.0.13 | 2.0.x | 17 | Maven 3 / 4.0 |
| 3.1.x | 3.1.12 | 2.0.x | 17 | Maven 3 / 4.0 |
| 3.2.x | 3.2.12 | 2.0.x | 17 | Maven 3 / 4.0 |
| 3.3.x | 3.3.13 | 2.0.x | 17 | Maven 3 / 4.0 |
| 3.4.x | 3.4.13 | 2.0.x | 17 | Maven 3 / 4.0 |
| 3.5.x | 3.5.16 | 2.0.x | 17 | Maven 3 / 4.0 |
| 4.0.x | 4.0.8 | 3.0.x | 21 | Maven 4 / 4.1 |
| 4.1.x | 4.1.0 | 3.0.x | 21 | Maven 4 / 4.1 |

## ddd4j-javalin

| Line | Javalin | ddd4j | JDK | Maven/POM |
|---|---|---|---:|---|
| 6.7.x | 6.7.0 | 1.0.x | 17 | Maven 3 / 4.0 |
| 7.1.x | 7.1.0 | 2.0.x | 17 | Maven 3 / 4.0 |
| 7.2.x | 7.2.3 | 3.0.x | 21 | Maven 4 / 4.1 |

## ddd4j-quarkus

| Line | Quarkus Platform | ddd4j | JDK | Maven/POM |
|---|---|---|---:|---|
| 3.3.x | 3.37.4 | 2.0.x | 17 | Maven 3 / 4.0 |
| 4.0.x | 3.38.2 | 3.0.x | 21 | Maven 4 / 4.1 |

4.0.x is the ddd4j-quarkus maintenance line name and does not mean Quarkus Platform 4.

## ddd4j-cloud primary combinations

| Cloud Line | Spring Cloud | Boot parent | ddd4j | Maven/POM |
|---|---|---|---|---|
| Hoxton.x | Hoxton.SR12 | 2.3.x | 1.0.x | Maven 3 / 4.0 |
| 2020.0.x | 2020.0.6 | 2.4.x | 1.0.x | Maven 3 / 4.0 |
| 2021.0.x | 2021.0.9 | 2.7.x | 1.0.x | Maven 3 / 4.0 |
| 2022.0.x | 2022.0.5 | 3.0.x | 2.0.x | Maven 3 / 4.0 |
| 2023.0.x | 2023.0.6 | 3.2.x | 2.0.x | Maven 3 / 4.0 |
| 2024.0.x | 2024.0.3 | 3.4.x | 2.0.x | Maven 3 / 4.0 |
| 2025.0.x | 2025.0.3 | 3.5.x | 2.0.x | Maven 3 / 4.0 |
| 2025.1.x | 2025.1.3 | 4.0.x | 3.0.x | Maven 4 / 4.1 |

## Evidence paths

- ddd4j-boot/config/consistency/ddd4j-boot-build-matrix.tsv
- ddd4j-cloud/scripts/compatibility/verify_cloud_release_matrix.py
- ddd4j-javalin per-feature-branch pom.xml
- ddd4j-quarkus per-feature-branch pom.xml
