<template lang="html">
    <div id="change-contact">
        <modal transition="modal fade" @ok="ok()" @cancel="cancel()" :title="title" large>
            <div class="container-fluid">
                <div class="row">
                    <form class="form-horizontal" name="declineForm">
                        <alert v-if="showError" type="danger"><strong>{{errorString}}</strong></alert>
                        <div class="col-sm-12">
                            <div class="mb-3">
                                <div class="row">
                                    <div class="col-sm-12">
                                        <label v-if=check_status() class="form-label"  for="Name">Details</label>
                                        <label v-else class="form-label"  for="Name">Provide Reason for the proposed decline </label>
                                        <textarea style="width: 70%;" class="form-control" name="reason" v-model="decline.reason"></textarea>
                                    </div>
                                </div>
                            </div>
                            <div class="mb-3">
                                <div class="row">
                                    <div class="col-sm-12">
                                        <label v-if=check_status() class="form-label"  for="Name">CC email</label>
                                        <label v-else class="form-label"  for="Name">Proposed CC email</label>
                                        <input type="text" style="width: 70%;" class="form-control" name="cc_email" v-model="decline.cc_email"/>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </form>
                </div>
            </div>
            <template #footer>
                <button type="button" v-if="decliningProposal" disabled class="btn btn-primary" @click="ok"><i class="fa fa-spinner fa-spin"></i> Processing</button>
                <button type="button" v-else class="btn btn-primary" @click="ok">Ok</button>
                <button type="button" class="btn btn-secondary" @click="cancel">Cancel</button>
            </template>
        </modal>
    </div>
</template>

<script>
import $ from 'jquery'
import modal from '@vue-utils/bootstrap-modal.vue'
import alert from '@vue-utils/alert.vue'
import {helpers,api_endpoints} from "@/utils/hooks.js"
export default {
    name:'Decline-Proposal',
    components:{
        modal,
        alert
    },
    props:{
            proposal_id:{
                type:Number,
                required: true
            },
            processing_status:{
                type:String,
                required: true
            },
    },
    data:function () {
        return {
            isModalOpen:false,
            form:null,
            decline: {},
            decliningProposal: false,
            errors: false,
            validation_form: null,
            errorString: '',
            successString: '',
            success:false,
        }
    },
    computed: {
        showError: function() {
            var vm = this;
            return vm.errors;
        },
        title: function(){
            return this.processing_status == 'With Approver' ? 'Decline': 'Proposed Decline';
        }
    },
    methods:{
        ok:function () {
            let vm =this;
            if($(vm.form).valid()){
                vm.errors = false;
                vm.sendData();
            } else {
                vm.errorString = "Missing required fields.";
                vm.errors = true;
            }
        },
        cancel:function () {
            this.close();
        },
        close:function () {
            this.isModalOpen = false;
            this.decline = {};
            this.errors = false;
            $('.has-error').removeClass('has-error');
            this.validation_form.resetForm();
        },

        check_status: function (){
            let vm= this;
            if (vm.processing_status == 'With Approver')
                return true;
            else
                return false;

        },
        sendData:function(){
            let vm = this;
            vm.errors = false;
            let decline = JSON.parse(JSON.stringify(vm.decline));
            vm.decliningProposal = true;
            if (vm.processing_status != 'With Approver'){
                 fetch(helpers.add_endpoint_json(api_endpoints.proposals, vm.proposal_id + '/proposed_decline'), {
                    method: 'POST',
                    headers: {
                    'Content-Type': 'application/x-www-form-urlencoded' // emulateJSON
                    },
                    body: new URLSearchParams(decline)
                })
                .then(response => {
                    if (!response.ok) throw response;
                    return response.json();
                })
                .then(response => {
                    vm.decliningProposal = false;
                    vm.close();
                    vm.$emit('refreshFromResponse', response);
                    vm.$router.push({ path: '/internal' }); // Navigate to dashboard after propose decline.
                })
                .catch(async error => {
                    vm.errors = true;
                    vm.decliningProposal = false;
                    try {
                    const errData = await error.json();
                    vm.errorString = errData;
                    } catch {
                    vm.errorString = 'An unexpected error occurred.';
                    }
                });
            }
            else{
                fetch(helpers.add_endpoint_json(api_endpoints.proposals, vm.proposal_id + '/final_decline'), {
                    method: 'POST',
                    headers: {
                    'Content-Type': 'application/x-www-form-urlencoded' // emulateJSON
                    },
                    body: new URLSearchParams(decline)
                })
                .then(response => {
                    if (!response.ok) throw response;
                    return response.json();
                })
                .then(response => {
                    vm.decliningProposal = false;
                    vm.close();
                    vm.$emit('refreshFromResponse', response);
                })
                .catch(async error => {
                    vm.errors = true;
                    vm.decliningProposal = false;
                    try {
                    const errData = await error.json();
                    vm.errorString = errData;
                    } catch {
                    vm.errorString = 'An unexpected error occurred.';
                    }
                });
            }
        },
        addFormValidations: function() {
            let vm = this;
            vm.validation_form = $(vm.form).validate({
                rules: {
                    reason:"required",
                },
            });
       },
       eventListerners:function () {
       }
   },
   mounted:function () {
       let vm =this;
       vm.form = document.forms.declineForm;
       vm.addFormValidations();
   }
}
</script>

<style lang="css">
</style>
