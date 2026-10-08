var site_url = location.origin

export default {
    organisations: '/api/organisations.json',
    organisation_requests: '/api/organisation_requests.json',
    organisation_contacts: '/api/organisation_contacts.json',
    organisation_access_group_members: '/api/organisation_access_group_members',
    apiary_organisation_access_group_members: '/api/apiary_organisation_access_group_members',
    users_api: '/api/users',
    users: '/api/users.json',
    profile: '/api/profile',
    my_user_details: '/api/my_user_details/',
    countries: '/api/countries',
    proposals:"/api/proposal.json",
    approvals:"/api/approvals.json",
    referrals:"/api/referrals.json",
    compliances:"/api/compliances.json",
    proposal_standard_requirements:"/api/proposal_standard_requirements.json",
    disturbance_standard_requirements:"/api/proposal_standard_requirements/disturbance_standard_requirements.json",
    apiary_standard_requirements:"/api/proposal_standard_requirements/apiary_standard_requirements.json",
    proposal_requirements:"/api/proposal_requirements.json",
    amendment_request:"/api/amendment_request.json",
    regions:"/api/regions.json",
    activity_matrix:"/api/activity_matrix.json",
    application_types:"/api/application_types.json",
    searchable_application_types:"/api/application_types/searchable_application_types.json",
    person_org_lookup: '/api/person_org_lookup',
    // used in internal and external dashboards
    proposals_paginated_external:   "/api/proposal_paginated/proposals_external/?format=datatables",
    approvals_paginated_external:   "/api/approval_paginated/approvals_external/?format=datatables",
    compliances_paginated_external: "/api/compliance_paginated/compliances_external/?format=datatables",
    proposals_paginated_internal:   "/api/proposal_paginated/proposals_internal/?format=datatables",
    referrals_paginated_internal:   "/api/proposal_paginated/referrals_internal/?format=datatables",
    filter_list:                    "/api/proposal/filter_list.json",
    filter_list_approvals:          "/api/approvals/filter_list.json",
    filter_list_compliances:        "/api/compliances/filter_list.json",
    filter_list_referrals:          "/api/referrals/filter_list.json",

    discard_proposal:function (id) {
      return `/api/proposal/${id}/discard/`;
    },
    site_url: site_url,
    system_name: 'Disturbance Approval System',
    
    // Apiary specific endpoints
    apiary_referral_groups:"/api/apiary_referral_groups.json",
    proposal_apiary:"/api/proposal_apiary.json",
    apiary_referrals:"/api/apiary_referrals.json",
    apiary_site_transfer_fees:"/api/get_site_transfer_fees",

    history_version_compare_field: "/api/history/compare/field/",
    history_version_compare: "/api/history/compare/",
    history_versions: "/api/history/versions/",
    history_version: "/api/history/version/",
    geocoding_address_search: "/api/geocoding_address_search/",
    get_organisation_id: function (org_id) {
      return `/api/get_organisation_id/?org_id=${org_id}`
    },

    is_new_user: '/api/is_new_user/',
}
