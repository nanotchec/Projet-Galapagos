def generate_v1_35_recommendation(canonical_path_results):
    if canonical_path_results["canonical_path_status"] == "CANONICAL_SOURCE_PATH_RECOVERED":
        return "use recovered canonical path to rerun V1.32.4 and V1.33 diagnostics"
    else:
        return "retire V1.32.4 as canonical source unless historical selected-trade artifacts are recovered; define a new reproducible canonical universe from the EV-strict rebuild path"
