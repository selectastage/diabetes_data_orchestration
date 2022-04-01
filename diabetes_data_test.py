import pandas as pd
import requests
import csv
import re

def request_ct(url):
    """Performs a get request that provides a (somewhat) useful error message."""
    try:
        response = requests.get(url)
    except ImportError:
        raise ImportError(
            "Couldn't retrieve the data, check your search expression or try again later."
        )
    else:
        return response

def json_handler(url):
    """Returns request in JSON (dict) format"""
    return request_ct(url).json()

def csv_handler(url):
    """Returns request in CSV (list of records) format"""

    response = request_ct(url)
    decoded_content = response.content.decode("utf-8")

    split_by_blank = re.split(r"\n\s*\n", decoded_content)  # Extracts header info
    cr = csv.reader(split_by_blank[1].splitlines(), delimiter=",")
    records = list(cr)

    return records



class ClinicalTrials:
    """ClinicalTrials API client
    Provides functions to easily access the ClinicalTrials.gov API
    (https://clinicaltrials.gov/api/)
    in Python.
    Attributes:
        study_fields: List of all study fields you can use in your query.
        api_info: Tuple containing the API version number and the last
        time the database was updated.
    """

    _BASE_URL = "https://clinicaltrials.gov/api/"
    _INFO = "info/"
    _QUERY = "query/"
    _JSON = "fmt=json"
    _CSV = "fmt=csv"

    def __init__(self):
        self.api_info = self.__api_info()

    @property
    def study_fields(self):
        fields_list = json_handler(
            f"{self._BASE_URL}{self._INFO}study_fields_list?{self._JSON}"
        )
        return fields_list["StudyFields"]["Fields"]

    def __api_info(self):
        """Returns information about the API"""
        last_updated = json_handler(
            f"{self._BASE_URL}{self._INFO}data_vrs?{self._JSON}"
        )["DataVrs"]
        api_version = json_handler(f"{self._BASE_URL}{self._INFO}api_vrs?{self._JSON}")[
            "APIVrs"
        ]

        return api_version, last_updated

    def get_full_studies(self, search_expr, max_studies=50):
        """Returns all content for a maximum of 100 study records.
        Retrieves information from the full studies endpoint, which gets all study fields.
        This endpoint can only output JSON (Or not-supported XML) format and does not allow
        requests for more than 100 studies at once.
        Args:
            search_expr (str): A string containing a search expression as specified by
                `their documentation <https://clinicaltrials.gov/api/gui/ref/syntax#searchExpr>`_.
            max_studies (int): An integer indicating the maximum number of studies to return.
                Defaults to 50.
        Returns:
            dict: Object containing the information queried with the search expression.
        Raises:
            ValueError: The number of studies can only be between 1 and 100
        """
        if max_studies > 100 or max_studies < 1:
            raise ValueError("The number of studies can only be between 1 and 100")

        req = f"full_studies?expr={search_expr}&max_rnk={max_studies}&{self._JSON}"

        full_studies = json_handler(f"{self._BASE_URL}{self._QUERY}{req}")

        return full_studies

    def get_study_fields(self, search_expr, fields, max_studies=50, fmt="csv"):
        """Returns study content for specified fields
        Retrieves information from the study fields endpoint, which acquires specified information
        from a large (max 1000) studies. To see a list of all possible fields, check the class'
        study_fields attribute.
        Args:
            search_expr (str): A string containing a search expression as specified by
                `their documentation <https://clinicaltrials.gov/api/gui/ref/syntax#searchExpr>`_.
            fields (list(str)): A list containing the desired information fields.
            max_studies (int): An integer indicating the maximum number of studies to return.
                Defaults to 50.
            fmt (str): A string indicating the output format, csv or json. Defaults to csv.
        Returns:
            Either a dict, if fmt='json', or a list of records (e.g. a list of lists), if fmt='csv.
            Both containing the maximum number of study fields queried using the specified search expression.
        Raises:
            ValueError: The number of studies can only be between 1 and 1000
            ValueError: One of the fields is not valid! Check the study_fields attribute
                for a list of valid ones.
            ValueError: Format argument has to be either 'csv' or 'json'
        """
        if max_studies > 1000 or max_studies < 1:
            raise ValueError("The number of studies can only be between 1 and 1000")
        elif not set(fields).issubset(self.study_fields):
            raise ValueError(
                "One of the fields is not valid! Check the study_fields attribute for a list of valid ones."
            )
        else:
            concat_fields = ",".join(fields)
            req = f"study_fields?expr={search_expr}&max_rnk={max_studies}&fields={concat_fields}"
            if fmt == "csv":
                url = f"{self._BASE_URL}{self._QUERY}{req}&{self._CSV}"
                return csv_handler(url)

            elif fmt == "json":
                url = f"{self._BASE_URL}{self._QUERY}{req}&{self._JSON}"
                return json_handler(url)

            else:
                raise ValueError("Format argument has to be either 'csv' or 'json'")

    def get_study_count(self, search_expr):
        """Returns study count for specified search expression
        Retrieves the count of studies matching the text entered in search_expr.
        Args:
            search_expr (str): A string containing a search expression as specified by
                `their documentation <https://clinicaltrials.gov/api/gui/ref/syntax#searchExpr>`_.
        Returns:
            An integer
        Raises:
            ValueError: The search expression cannot be blank.
        """
        if not set(search_expr):
            raise ValueError("The search expression cannot be blank.")
        else:
            req = f"study_fields?expr={search_expr}&max_rnk=1&fields=NCTId"
            url = f"{self._BASE_URL}{self._QUERY}{req}&{self._JSON}"
            returned_data = json_handler(url)
            study_count = returned_data["StudyFieldsResponse"]["NStudiesFound"]
            return study_count

    def __repr__(self):
        return f"ClinicalTrials.gov client v{self.api_info[0]}, database last updated {self.api_info[1]}"

ct = ClinicalTrials()

# Get 50 full studies related to Coronavirus and COVID in json format.
ct.get_full_studies(search_expr="Diabetes", max_studies=5)

# Get the NCTId, Condition and Brief title fields from 500 studies related to Coronavirus and Covid, in csv format.
diabetes_fields = ct.get_study_fields(
    search_expr= "Diabetes",
    fields=[
    "NCTId", 
    "Condition", 
    "EnrollmentCount",
    "InterventionName", "PrimaryOutcomeMeasure","OutcomeMeasurementValue"],
    max_studies=500,
    fmt="csv",
    )

# Get the count of studies related to Coronavirus and COVID.
# ClinicalTrials limits API queries to 1000 records
# Count of studies may be useful to build loops when you want to retrieve more than 1000 records

#ct.get_study_count(search_expr="Coronavirus+COVID")

# Read the csv data in Pandas

df = pd.DataFrame.from_records(diabetes_fields[1:], columns=diabetes_fields[0])

print(print([df.iloc[10].values]))

fields = {
  "StudyFields":{
    "APIVrs":"1.01.05",
    "Fields":[
      "Acronym",
      "AgreementOtherDetails",
      "AgreementPISponsorEmployee",
      "AgreementRestrictionType",
      "AgreementRestrictiveAgreement",
      "ArmGroupDescription",
      "ArmGroupInterventionName",
      "ArmGroupLabel",
      "ArmGroupType",
      "AvailIPDComment",
      "AvailIPDId",
      "AvailIPDType",
      "AvailIPDURL",
      "BaselineCategoryTitle",
      "BaselineClassDenomCountGroupId",
      "BaselineClassDenomCountValue",
      "BaselineClassDenomUnits",
      "BaselineClassTitle",
      "BaselineDenomCountGroupId",
      "BaselineDenomCountValue",
      "BaselineDenomUnits",
      "BaselineGroupDescription",
      "BaselineGroupId",
      "BaselineGroupTitle",
      "BaselineMeasureCalculatePct",
      "BaselineMeasureDenomCountGroupId",
      "BaselineMeasureDenomCountValue",
      "BaselineMeasureDenomUnits",
      "BaselineMeasureDenomUnitsSelected",
      "BaselineMeasureDescription",
      "BaselineMeasureDispersionType",
      "BaselineMeasureParamType",
      "BaselineMeasurePopulationDescription",
      "BaselineMeasureTitle",
      "BaselineMeasureUnitOfMeasure",
      "BaselineMeasurementComment",
      "BaselineMeasurementGroupId",
      "BaselineMeasurementLowerLimit",
      "BaselineMeasurementSpread",
      "BaselineMeasurementUpperLimit",
      "BaselineMeasurementValue",
      "BaselinePopulationDescription",
      "BaselineTypeUnitsAnalyzed",
      "BioSpecDescription",
      "BioSpecRetention",
      "BriefSummary",
      "BriefTitle",
      "CentralContactEMail",
      "CentralContactName",
      "CentralContactPhone",
      "CentralContactPhoneExt",
      "CentralContactRole",
      "CollaboratorClass",
      "CollaboratorName",
      "CompletionDate",
      "CompletionDateType",
      "Condition",
      "ConditionAncestorId",
      "ConditionAncestorTerm",
      "ConditionBrowseBranchAbbrev",
      "ConditionBrowseBranchName",
      "ConditionBrowseLeafAsFound",
      "ConditionBrowseLeafId",
      "ConditionBrowseLeafName",
      "ConditionBrowseLeafRelevance",
      "ConditionMeshId",
      "ConditionMeshTerm",
      "DelayedPosting",
      "DesignAllocation",
      "DesignInterventionModel",
      "DesignInterventionModelDescription",
      "DesignMasking",
      "DesignMaskingDescription",
      "DesignObservationalModel",
      "DesignPrimaryPurpose",
      "DesignTimePerspective",
      "DesignWhoMasked",
      "DetailedDescription",
      "DispFirstPostDate",
      "DispFirstPostDateType",
      "DispFirstSubmitDate",
      "DispFirstSubmitQCDate",
      "EligibilityCriteria",
      "EnrollmentCount",
      "EnrollmentType",
      "EventGroupDeathsNumAffected",
      "EventGroupDeathsNumAtRisk",
      "EventGroupDescription",
      "EventGroupId",
      "EventGroupOtherNumAffected",
      "EventGroupOtherNumAtRisk",
      "EventGroupSeriousNumAffected",
      "EventGroupSeriousNumAtRisk",
      "EventGroupTitle",
      "EventsDescription",
      "EventsFrequencyThreshold",
      "EventsTimeFrame",
      "ExpAccTypeIndividual",
      "ExpAccTypeIntermediate",
      "ExpAccTypeTreatment",
      "ExpandedAccessNCTId",
      "ExpandedAccessStatusForNCTId",
      "FDAAA801Violation",
      "FlowAchievementComment",
      "FlowAchievementGroupId",
      "FlowAchievementNumSubjects",
      "FlowAchievementNumUnits",
      "FlowDropWithdrawComment",
      "FlowDropWithdrawType",
      "FlowGroupDescription",
      "FlowGroupId",
      "FlowGroupTitle",
      "FlowMilestoneComment",
      "FlowMilestoneType",
      "FlowPeriodTitle",
      "FlowPreAssignmentDetails",
      "FlowReasonComment",
      "FlowReasonGroupId",
      "FlowReasonNumSubjects",
      "FlowReasonNumUnits",
      "FlowRecruitmentDetails",
      "FlowTypeUnitsAnalyzed",
      "Gender",
      "GenderBased",
      "GenderDescription",
      "HasExpandedAccess",
      "HealthyVolunteers",
      "IPDSharing",
      "IPDSharingAccessCriteria",
      "IPDSharingDescription",
      "IPDSharingInfoType",
      "IPDSharingTimeFrame",
      "IPDSharingURL",
      "InterventionAncestorId",
      "InterventionAncestorTerm",
      "InterventionArmGroupLabel",
      "InterventionBrowseBranchAbbrev",
      "InterventionBrowseBranchName",
      "InterventionBrowseLeafAsFound",
      "InterventionBrowseLeafId",
      "InterventionBrowseLeafName",
      "InterventionBrowseLeafRelevance",
      "InterventionDescription",
      "InterventionMeshId",
      "InterventionMeshTerm",
      "InterventionName",
      "InterventionOtherName",
      "InterventionType",
      "IsFDARegulatedDevice",
      "IsFDARegulatedDrug",
      "IsPPSD",
      "IsUSExport",
      "IsUnapprovedDevice",
      "Keyword",
      "LargeDocDate",
      "LargeDocFilename",
      "LargeDocHasICF",
      "LargeDocHasProtocol",
      "LargeDocHasSAP",
      "LargeDocLabel",
      "LargeDocTypeAbbrev",
      "LargeDocUploadDate",
      "LastKnownStatus",
      "LastUpdatePostDate",
      "LastUpdatePostDateType",
      "LastUpdateSubmitDate",
      "LeadSponsorClass",
      "LeadSponsorName",
      "LimitationsAndCaveatsDescription",
      "LocationCity",
      "LocationContactEMail",
      "LocationContactName",
      "LocationContactPhone",
      "LocationContactPhoneExt",
      "LocationContactRole",
      "LocationCountry",
      "LocationFacility",
      "LocationState",
      "LocationStatus",
      "LocationZip",
      "MaximumAge",
      "MinimumAge",
      "NCTId",
      "NCTIdAlias",
      "OfficialTitle",
      "OrgClass",
      "OrgFullName",
      "OrgStudyId",
      "OrgStudyIdDomain",
      "OrgStudyIdLink",
      "OrgStudyIdType",
      "OtherEventAssessmentType",
      "OtherEventNotes",
      "OtherEventOrganSystem",
      "OtherEventSourceVocabulary",
      "OtherEventStatsGroupId",
      "OtherEventStatsNumAffected",
      "OtherEventStatsNumAtRisk",
      "OtherEventStatsNumEvents",
      "OtherEventTerm",
      "OtherOutcomeDescription",
      "OtherOutcomeMeasure",
      "OtherOutcomeTimeFrame",
      "OutcomeAnalysisCILowerLimit",
      "OutcomeAnalysisCILowerLimitComment",
      "OutcomeAnalysisCINumSides",
      "OutcomeAnalysisCIPctValue",
      "OutcomeAnalysisCIUpperLimit",
      "OutcomeAnalysisCIUpperLimitComment",
      "OutcomeAnalysisDispersionType",
      "OutcomeAnalysisDispersionValue",
      "OutcomeAnalysisEstimateComment",
      "OutcomeAnalysisGroupDescription",
      "OutcomeAnalysisGroupId",
      "OutcomeAnalysisNonInferiorityComment",
      "OutcomeAnalysisNonInferiorityType",
      "OutcomeAnalysisOtherAnalysisDescription",
      "OutcomeAnalysisPValue",
      "OutcomeAnalysisPValueComment",
      "OutcomeAnalysisParamType",
      "OutcomeAnalysisParamValue",
      "OutcomeAnalysisStatisticalComment",
      "OutcomeAnalysisStatisticalMethod",
      "OutcomeAnalysisTestedNonInferiority",
      "OutcomeCategoryTitle",
      "OutcomeClassDenomCountGroupId",
      "OutcomeClassDenomCountValue",
      "OutcomeClassDenomUnits",
      "OutcomeClassTitle",
      "OutcomeDenomCountGroupId",
      "OutcomeDenomCountValue",
      "OutcomeDenomUnits",
      "OutcomeGroupDescription",
      "OutcomeGroupId",
      "OutcomeGroupTitle",
      "OutcomeMeasureAnticipatedPostingDate",
      "OutcomeMeasureCalculatePct",
      "OutcomeMeasureDenomUnitsSelected",
      "OutcomeMeasureDescription",
      "OutcomeMeasureDispersionType",
      "OutcomeMeasureParamType",
      "OutcomeMeasurePopulationDescription",
      "OutcomeMeasureReportingStatus",
      "OutcomeMeasureTimeFrame",
      "OutcomeMeasureTitle",
      "OutcomeMeasureType",
      "OutcomeMeasureTypeUnitsAnalyzed",
      "OutcomeMeasureUnitOfMeasure",
      "OutcomeMeasurementComment",
      "OutcomeMeasurementGroupId",
      "OutcomeMeasurementLowerLimit",
      "OutcomeMeasurementSpread",
      "OutcomeMeasurementUpperLimit",
      "OutcomeMeasurementValue",
      "OverallOfficialAffiliation",
      "OverallOfficialName",
      "OverallOfficialRole",
      "OverallStatus",
      "OversightHasDMC",
      "PatientRegistry",
      "Phase",
      "PointOfContactEMail",
      "PointOfContactOrganization",
      "PointOfContactPhone",
      "PointOfContactPhoneExt",
      "PointOfContactTitle",
      "PrimaryCompletionDate",
      "PrimaryCompletionDateType",
      "PrimaryOutcomeDescription",
      "PrimaryOutcomeMeasure",
      "PrimaryOutcomeTimeFrame",
      "ReferenceCitation",
      "ReferencePMID",
      "ReferenceType",
      "RemovedCountry",
      "ResponsiblePartyInvestigatorAffiliation",
      "ResponsiblePartyInvestigatorFullName",
      "ResponsiblePartyInvestigatorTitle",
      "ResponsiblePartyOldNameTitle",
      "ResponsiblePartyOldOrganization",
      "ResponsiblePartyType",
      "ResultsFirstPostDate",
      "ResultsFirstPostDateType",
      "ResultsFirstPostedQCCommentsDate",
      "ResultsFirstPostedQCCommentsDateType",
      "ResultsFirstSubmitDate",
      "ResultsFirstSubmitQCDate",
      "RetractionPMID",
      "RetractionSource",
      "SamplingMethod",
      "SecondaryId",
      "SecondaryIdDomain",
      "SecondaryIdLink",
      "SecondaryIdType",
      "SecondaryOutcomeDescription",
      "SecondaryOutcomeMeasure",
      "SecondaryOutcomeTimeFrame",
      "SeeAlsoLinkLabel",
      "SeeAlsoLinkURL",
      "SeriousEventAssessmentType",
      "SeriousEventNotes",
      "SeriousEventOrganSystem",
      "SeriousEventSourceVocabulary",
      "SeriousEventStatsGroupId",
      "SeriousEventStatsNumAffected",
      "SeriousEventStatsNumAtRisk",
      "SeriousEventStatsNumEvents",
      "SeriousEventTerm",
      "StartDate",
      "StartDateType",
      "StatusVerifiedDate",
      "StdAge",
      "StudyFirstPostDate",
      "StudyFirstPostDateType",
      "StudyFirstSubmitDate",
      "StudyFirstSubmitQCDate",
      "StudyPopulation",
      "StudyType",
      "SubmissionMCPReleaseN",
      "SubmissionReleaseDate",
      "SubmissionResetDate",
      "SubmissionUnreleaseDate",
      "TargetDuration",
      "UnpostedEventDate",
      "UnpostedEventType",
      "UnpostedResponsibleParty",
      "VersionHolder",
      "WhyStopped"
    ]
  }
}