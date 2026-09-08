<template id="proposal_requirements">
    <div>
        <template v-if="isFinalised">
            <div class="col-md-12 alert alert-success" v-if="proposal.processing_status == 'Approved'">
                <div v-if="proposal.proposal_apiary">
                    <p>The licence has been issued and has been emailed to {{proposal.applicant.name}}</p>
                    <p>Expiry date: {{approvalExpiryDate}}</p>
                    <p>Licence: <a target="_blank" :href="proposal.permit">licence.pdf</a></p>
                </div>
                <div v-else>
                    <p>The approval has been issued and has been emailed to {{proposal.applicant.name}}</p>
                    <p>Expiry date: {{approvalExpiryDate}}</p>
                    <p>Permit: <a target="_blank" :href="proposal.permit">approval.pdf</a></p>
                </div>
            </div>
            <div v-else class="col-md-12 alert alert-warning">
                <div v-if="proposal.proposal_apiary">
                    <p>The application was declined. The decision was emailed to {{proposal.applicant.name}}</p>
                </div>
                <div v-else>
                    <p>The proposal was declined. The decision was emailed to {{proposal.applicant.name}}</p>
                </div>
            </div>
        </template>

        <template v-if="proposal.proposal_apiary">
            <FormSection :formCollapse="false" label="Site(s)" Index="sites">
                <ComponentSiteSelection
                    :is_internal="true"
                    :is_external="false"
                    :key="component_site_selection_key"
                    :show_col_checkbox="showColCheckbox"
                    :enable_col_checkbox="false"
                    :show_col_site="false"
                    :show_col_site_when_submitted="true"
                    :show_col_status_when_submitted="true"
                    :apiary_proposal_id="proposal.proposal_apiary.id"
                />
            </FormSection>
        </template>
        <template v-else>
            <FormSection :formCollapse="false" label="Level of Approval" Index="level_of_approval">
                <div v-if="!isFinalised">
                    <p><strong>Level of approval: {{proposal.approval_level}}</strong></p>

                    <div v-if="isApprovalLevel">
                        <p v-if="proposal.approval_level_document"><strong>Attach documents:</strong> <a :href="proposal.approval_level_document[1]" target="_blank">{{proposal.approval_level_document[0]}}</a>
                        <span>
                            <a @click="removeFile()" class="fa fa-trash-o" title="Remove file" style="cursor: pointer; color:red;"></a>
                        </span></p>
                        <div v-else>
                            <p><strong>Attach documents:</strong></p>
                            <div class="col-sm-12">
                            <span class="btn btn-info btn-file float-start">
                            Attach File <input type="file" ref="uploadedFile" @change="readFile()"/>
                            </span>
                            <!--<span class="float-start" style="margin-left:10px;margin-top:10px;">{{uploadedFileName()}}</span>-->

                            </div>
                            <div class="row"><p></p></div>
                            <div class="row"><p></p></div>
                            <div class="row"><p></p></div>

                            <p>
                                <strong>Comments (if no approval attached)</strong>
                            </p>
                            <p>
                                <textarea name="approval_level_comments"  v-model="proposal.approval_level_comment" class="form-control" style="width:70%;"></textarea>
                            </p>
                        </div>
                    </div>
                </div>

                <div v-if="isFinalised">
                    <p><strong>Level of approval: {{proposal.approval_level}}</strong></p>

                    <div v-if="isApprovalLevel">
                        <p v-if="proposal.approval_level_document"><strong>Attach documents: </strong><a :href="proposal.approval_level_document[1]" target="_blank">{{proposal.approval_level_document[0]}}</a>
                        </p>
                        <p v-if="proposal.approval_level_comment"><strong>Comments: {{proposal.approval_level_comment}}</strong>
                        </p>
                    </div>
                </div>
            </FormSection>
        </template>

        <FormSection :formCollapse="false" :label="decision_label" Index="decision">
            <template v-if="!proposal.proposed_decline_status">
                <template v-if="isFinalised">
                    <p><strong>Decision: Issue</strong></p>
                    <p><strong>Start date: {{proposal.proposed_issuance_approval.start_date}}</strong></p>
                    <p><strong>Expiry date: {{proposal.proposed_issuance_approval.expiry_date}}</strong></p>
                    <p><strong>CC emails: {{proposal.proposed_issuance_approval.cc_email}}</strong></p>
                </template>
                <template v-else>
                    <p><strong>Proposed decision: Issue</strong></p>
                    <p><strong>Proposed start date: {{proposal.proposed_issuance_approval.start_date}}</strong></p>
                    <p><strong>Proposed expiry date: {{proposal.proposed_issuance_approval.expiry_date}}</strong></p>
                    <p><strong>Proposed cc emails: {{proposal.proposed_issuance_approval.cc_email}}</strong></p>
                </template>
            </template>
            <template v-else>
                <strong v-if="!isFinalised">Proposed decision: Decline</strong>
                <strong v-else>Decision: Decline</strong>
            </template>
        </FormSection>
    </div>
</template>
<script>
import { v4 as uuid } from 'uuid';
import {
    api_endpoints,
    helpers
}
from '@/utils/hooks'
import ComponentSiteSelection from '@/components/common/apiary/component_site_selection.vue'
import FormSection from "@/components/forms/section_toggle.vue"
import $ from 'jquery';

export default {
    name: 'InternalProposalRequirements',
    props: {
        proposal: Object
    },
    data: function() {
        return {
            proposedDecision: "proposal-decision-"+uuid(),
            proposedLevel: "proposal-level-"+uuid(),
            uploadedFile: null,
            component_site_selection_key: '',
            apiary_sites: {},
        }
    },
    components:{
        FormSection,
        ComponentSiteSelection,
    },
    computed:{
        /*
        approvalStartDate: function() {
            let returnDate = null;
            if (this.proposal && this.proposal.approval) {
                returnDate = moment(this.proposal.approval.start_date, 'YYYY-MM-DD').format('DD/MM/YYYY');
            }
            return returnDate;
        },
        */
        approvalExpiryDate: function() {
            let returnDate = null;
            if (this.proposal && this.proposal.approval) {
                returnDate = moment(this.proposal.approval.expiry_date, 'YYYY-MM-DD').format('DD/MM/YYYY');
            }
            return returnDate;
        },
        hasAssessorMode(){
            return this.proposal.assessor_mode.has_assessor_mode;
        },
        isFinalised: function(){
            return this.proposal.processing_status == 'Approved' || this.proposal.processing_status == 'Declined';
        },
        isApprovalLevel:function(){
            return this.proposal.approval_level != null ? true : false;
        },
        showColCheckbox: function() {
            let checked = true;
            if (this.proposal.proposal_apiary.application_type !== 'Site Transfer') {
                checked = false;
            }
            return checked;
        },
        decision_label: function(){
            return this.isFinalised == true ? 'Decision' : 'Proposed Decision';
        }

    },
    methods:{
        getApiarySites: function() {
            if (this.proposal && this.proposal.proposal_apiary) {

                let url_sites = '/api/proposal_apiary/' + this.proposal.proposal_apiary.id + '/apiary_sites/'
                fetch(url_sites).then(
                    async (response) => {
                        if (response.ok) {
                            let apiary_sites_req = await response.json();
                            this.apiary_sites = JSON.parse(JSON.stringify(apiary_sites_req))
                        }
                    }
                ).catch((error) => {
                    console.log(error);
                })
            }
        },
        updateComponentSiteSelectionKey: function(){
            console.log('in updateComponentSiteSelectionKey')
            this.component_site_selection_key = uuid()
        },
        readFile: function() {
            let vm = this;
            let _file = null;
            var input = $(vm.$refs.uploadedFile)[0];
            if (input.files && input.files[0]) {
                var reader = new FileReader();
                reader.readAsDataURL(input.files[0]);
                reader.onload = function(e) {
                    _file = e.target.result;
                };
                _file = input.files[0];
            }
            vm.uploadedFile = _file;
            vm.save()
        },
        removeFile: function(){
            let vm = this;
            vm.uploadedFile = null;
            vm.save()
        },
        save: function(){
            let vm = this;
                let data = new FormData(vm.form);
                data.append('approval_level_document', vm.uploadedFile)
                if (vm.proposal.approval_level_document) {
                    data.append('approval_level_document_name', vm.proposal.approval_level_document[0])
                }

                fetch(helpers.add_endpoint_json(api_endpoints.proposals, vm.proposal.id + '/approval_level_document'), {
                method: 'POST',
                body: data // FormData handles headers automatically
                })
                .then(response => {
                    if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
                    return response.json();
                })
                .then(res => {
                    //vm.proposal = res;
                    Object.assign(vm.proposal, res);
                    vm.$emit('refreshFromResponse', res);
                })
                .catch(async err => {
                    console.log(err);
                    let errorText = 'An unexpected error occurred.';
                    try {
                        const errData = await err.json();
                        errorText = errData;
                    } catch { console.log('Error parsing error response'); }
                    
                    swal.fire({
                        title:'Submit Error', 
                        text:errorText,
                        icon:'error',
                        customClass: {
                            confirmButton: 'btn btn-primary',
                        },
                    });
            });
        },
        uploadedFileName: function() {
            return this.uploadedFile != null ? this.uploadedFile.name: '';
        },
        addRequirement(){
            this.$refs.requirement_detail.isModalOpen = true;
        },
        removeRequirement(_id){
            let vm = this;
           swal.fire({
                title: "Remove Requirement",
                text: "Are you sure you want to remove this requirement?",
                icon: "warning",
                showCancelButton: true,
                confirmButtonText: 'Remove Requirement',
                customClass: {
                    confirmButton: 'btn btn-primary',
                    cancelButton: 'btn btn-secondary',
                },
            }).then((swalresult) => {
                if(swalresult.isConfirmed){
                    fetch(helpers.add_endpoint_json(api_endpoints.proposal_requirements,_id),{
                        method: 'DELETE',
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    })
                    .then(async (response) => {
                        if (!response.ok) { return response.json().then(err => { throw err }); }
                        
                        vm.$refs.requirements_datatable.vmDataTable.ajax.reload();
                    }).catch((error) => {
                        console.log(error);
                    });
                }
            },(error) => {
                console.log(error);
            });
        },
    },
    mounted: function(){
        this.updateComponentSiteSelectionKey()
    },
    created: function() {
        let vm = this;
        vm.getApiarySites();
    }
}
</script>
<style scoped>
</style>
