import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import AnalysisResult, WhereClause

def seed_arm_data(db_path='metadata.db'):
    engine = create_engine(f'sqlite:///{db_path}')
    Session = sessionmaker(bind=engine)
    session = Session()

    print(f"[seed_arm_results] Seeding ARM metadata in {db_path}...")

    # 1. Seed Where Clauses
    where_clauses = [
        WhereClause(
            where_clause_id="WC_PARAMCD_PFS",
            dataset="ADTTE",
            variable="PARAMCD",
            filter_operator="EQ",
            filter_value="PFS"
        ),
        WhereClause(
            where_clause_id="WC_PARAMCD_OS",
            dataset="ADTTE",
            variable="PARAMCD",
            filter_operator="EQ",
            filter_value="OS"
        ),
        WhereClause(
            where_clause_id="WC_PARAMCD_IPFS",
            dataset="ADTTE",
            variable="PARAMCD",
            filter_operator="EQ",
            filter_value="iPFS"
        ),
        WhereClause(
            where_clause_id="WC_PARAMCD_BOR",
            dataset="ADRS",
            variable="PARAMCD",
            filter_operator="EQ",
            filter_value="BOR"
        ),
        WhereClause(
            where_clause_id="WC_PARAMCD_DOR",
            dataset="ADDOR",
            variable="PARAMCD",
            filter_operator="EQ",
            filter_value="DOR"
        ),
        WhereClause(
            where_clause_id="WC_PARAMCD_PFS_EMA",
            dataset="ADTTE",
            variable="PARAMCD",
            filter_operator="EQ",
            filter_value="PFS_EMA"
        )
    ]

    for wc in where_clauses:
        session.merge(wc)
    session.commit()
    print(f"[seed_arm_results] Seeded {len(where_clauses)} Where Clauses.")

    # 2. Seed Analysis Results (ARM Core)
    analysis_results = [
        # Primary PFS (WT population)
        AnalysisResult(
            analysis_id="ANA_PFS_WT_01",
            endpoint_id="EP_PFS_WT",
            dataset="ADTTE",
            paramcd="PFS",
            where_clause_id="WC_PARAMCD_PFS",
            stat_method="Stratified Cox Proportional Hazards Model",
            stat_test="Stratified Log-Rank Test",
            tfl_reference="Table 14.2.1.1",
            estimand_id="EST_PFS_WT",
            arm_display_label="Arm B vs Arm C (WT Population)"
        ),
        # Sensitivity Analysis PFS (EMA rules) (WT population)
        AnalysisResult(
            analysis_id="ANA_PFS_EMA_WT_01",
            endpoint_id="EP_PFS_WT",
            dataset="ADTTE",
            paramcd="PFS_EMA",
            where_clause_id="WC_PARAMCD_PFS_EMA",
            stat_method="Stratified Cox Proportional Hazards Model",
            stat_test="Stratified Log-Rank Test",
            tfl_reference="Table 14.2.1.1.1",
            estimand_id="EST_PFS_WT",
            arm_display_label="Arm B vs Arm C (WT Population, EMA Rules)"
        ),
        # Primary OS (WT population)
        AnalysisResult(
            analysis_id="ANA_OS_WT_01",
            endpoint_id="EP_OS_WT",
            dataset="ADTTE",
            paramcd="OS",
            where_clause_id="WC_PARAMCD_OS",
            stat_method="Stratified Cox Proportional Hazards Model",
            stat_test="Stratified Log-Rank Test",
            tfl_reference="Table 14.2.1.2",
            estimand_id="EST_OS_WT",
            arm_display_label="Arm B vs Arm C (WT Population)"
        ),
        # Primary OS for Arm A vs C
        AnalysisResult(
            analysis_id="ANA_OS_ARMA_01",
            endpoint_id="EP_PRM_OS_3",  # Ingested outcome for Arm A vs C OS
            dataset="ADTTE",
            paramcd="OS",
            where_clause_id="WC_PARAMCD_OS",
            stat_method="Stratified Cox Proportional Hazards Model",
            stat_test="Stratified Log-Rank Test",
            tfl_reference="Table 14.2.1.3",
            estimand_id="EST_OS_WT",  # Shares population/estimand characteristics
            arm_display_label="Arm A vs Arm C (WT Population)"
        ),
        # Exploratory iPFS (ITT population)
        AnalysisResult(
            analysis_id="ANA_IPFS_ITT_01",
            endpoint_id="EP_IPFS_ITT",
            dataset="ADTTE",
            paramcd="iPFS",
            where_clause_id="WC_PARAMCD_IPFS",
            stat_method="Unstratified Cox Model",
            stat_test="Unstratified Log-Rank Test",
            tfl_reference="Table 14.2.2.1",
            estimand_id="EST_IPFS_ITT",
            arm_display_label="Arm B vs Arm C (ITT Population)"
        ),
        # Secondary ORR
        AnalysisResult(
            analysis_id="ANA_ORR_ITT_01",
            endpoint_id="EP_SEC_BOR_1",
            dataset="ADRS",
            paramcd="BOR",
            where_clause_id="WC_PARAMCD_BOR",
            stat_method="Stratified Cochran-Mantel-Haenszel (CMH) Method",
            stat_test="Cochran-Mantel-Haenszel Test",
            tfl_reference="Table 14.2.3.1",
            estimand_id="EST_OS_WT",
            arm_display_label="Arm B vs Arm C (ITT-WT Population)"
        ),
        # Secondary DOR
        AnalysisResult(
            analysis_id="ANA_DOR_ITT_01",
            endpoint_id="EP_SEC_DOR_9",
            dataset="ADDOR",
            paramcd="DOR",
            where_clause_id="WC_PARAMCD_DOR",
            stat_method="Kaplan-Meier Methodology",
            stat_test="Kaplan-Meier Descriptive Statistics",
            tfl_reference="Table 14.2.3.2",
            estimand_id="EST_OS_WT",
            arm_display_label="Arm B vs Arm C (ITT-WT Population)"
        )
    ]

    for ar in analysis_results:
        session.merge(ar)
    session.commit()
    print("[seed_arm_results] Seeded 6 Analysis Results (ARM).")

    session.close()

if __name__ == '__main__':
    seed_arm_data()
