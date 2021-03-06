# Copyright 2015 Objectif Libre
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from decimal import *
import json

from django import http
from horizon import exceptions
from horizon import views

from cloudkittydashboard.api import cloudkitty as api

from openstack_dashboard.dashboards.identity.users \
    import forms as project_forms
from openstack_dashboard.dashboards.identity.users \
    import tables as project_table

import dateutil.relativedelta
import simplejson as json
import pytz
import time
import datetime
from dateutil import tz

from openstack_dashboard import api as napi
from openstack_dashboard.api import keystone
from collections import OrderedDict

class IndexView(views.APIView):

    # A very simple class-based view...
    template_name = 'project/rating/index.html'

    def get_data(self, request, context, *args, **kwargs):
        
        try:
            
            # services dict
            services = OrderedDict()
            services = ['compute','image','volume','network.bw.in','network.bw.out','network.floating','cloudstorage','instance.addon','tenant.addon']
            services_mapping = OrderedDict()
            
            # Mapping for a services
            services_mapping = {'compute': 'Compute', 'image': 'Image','volume': 'Block Storage (Volume)', 'network.bw.in': 'Network Transfer (inbound)', 'network.bw.out': 'Network Transfer (outbound)', 'network.floating': 'Floating IP Addresses', 'cloudstorage': 'Object Storage (Swift)', 'instance.addon': 'Compute Instance Add-On', 'tenant.addon': 'Project Add-On' }
    
            # get the tenant list of user
            tenants = napi.keystone.tenant_list(
                                    self.request,
                                    request.user.id,
                                    marker = '',
                                    admin=False)
    
            # get the tenant list from tuple
            for tenant_items in tenants:
    
                    # if not bool
                    if not isinstance(tenant_items, bool):
                        
                            # tenant entries
                            for tenant_final in tenant_items:
    
                                    # getting the correct tenant
                                    if hasattr(tenant_final, 'id'):
    
                                            if tenant_final.id == request.user.tenant_id:
    
                                                    # if timezone exists
                                                    if hasattr(tenant_final, 'timezone'):
    
                                                            tenant_timezone = tenant_final.timezone
    
                                                    # If no timezone
                                                    else:
                                                            tenant_timezone = 'UTC'
    
                                                    # cretion_date of tenant for cloudstorage calc
                                                    if hasattr(tenant_final, 'creation_date'):
    
                                                            start_period_cloud = tenant_final.creation_date
    
                                                            if isinstance(start_period_cloud, unicode):
    
                                                                    start_period_cloud = datetime.datetime.strptime(start_period_cloud, '%Y-%m-%d %H:%M:%S')
                                                                    
                                                    # assume date if no creation_date
                                                    else:
    
                                                            start_period_cloud = datetime.datetime.now - dateutil.relativedelta.relativedelta(months=1)
    
            self.tenant_timezone = tenant_timezone
            now = datetime.datetime.now(pytz.timezone(self.tenant_timezone))
            start_time_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
            start_date_week = now - dateutil.relativedelta.relativedelta(days=7)
            start_date_week = start_date_week.replace(hour=0, minute=0, second=0, microsecond=0)
            start_date_month = now - dateutil.relativedelta.relativedelta(months=1)
            start_date_month = start_date_month.replace(hour=0, minute=0, second=0, microsecond=0)
    
            # Add data to the context here...
            total = api.cloudkittyclient(request).reports.get_total(
                    tenant_id=request.user.tenant_id, begin=self.local2utc(start_time_today), end= self.local2utc(now)) or 0.00
    
            total_dict = {}
            total_dict = OrderedDict(total_dict)
            for service_items in services:
                    print service_items
                    totals = api.cloudkittyclient(request).reports.get_total(
                            tenant_id=request.user.tenant_id, service=service_items, begin=self.local2utc(start_time_today), end= self.local2utc(now)) or 0.00
                    service_items = services_mapping[service_items]
                    total_dict[service_items] = totals
    
            total_week = api.cloudkittyclient(request).reports.get_total(
                    tenant_id=request.user.tenant_id, begin=self.local2utc(start_date_week), end= self.local2utc(now)) or 0.00
    
            total_week_dict = {}
            total_week_dict = OrderedDict(total_week_dict)
            for service_items in services:
                    totals_week = api.cloudkittyclient(request).reports.get_total(
                            tenant_id=request.user.tenant_id, service=service_items, begin=self.local2utc(start_date_week), end= self.local2utc(now)) or 0.00
                    service_items = services_mapping[service_items]
                    total_week_dict[service_items] = totals_week
    
            total_month = api.cloudkittyclient(request).reports.get_total(
                    tenant_id=request.user.tenant_id, begin=self.local2utc(start_date_month), end= self.local2utc(now)) or 0.00
    
            total_month_dict = {}
            total_month_dict = OrderedDict(total_month_dict)
            for service_items in services:
                    totals_month = api.cloudkittyclient(request).reports.get_total(
                            tenant_id=request.user.tenant_id, service=service_items, begin=self.local2utc(start_date_month), end= self.local2utc(now)) or 0.00
                    service_items = services_mapping[service_items]
                    total_month_dict[service_items] = totals_month


	    # cloud resource section
            total_cloud = api.cloudkittyclient(request).reports.get_total(
                    tenant_id=request.user.tenant_id, begin=self.local2utc(start_period_cloud), end= self.local2utc(now)) or 0.00

	    # cloud resources section    
            total_cloud_dict = {}
            total_cloud_dict = OrderedDict(total_cloud_dict)
            for service_items in services:
                    totals_cloud = api.cloudkittyclient(request).reports.get_total(
                            tenant_id=request.user.tenant_id, service=service_items, begin=self.local2utc(start_period_cloud), end= self.local2utc(now)) or 0.00
                    service_items = services_mapping[service_items]
                    total_cloud_dict[service_items] = totals_cloud
 
        except:
   
            # services dict
            services = OrderedDict()
            services = ['compute','image','volume','network.bw.in','network.bw.out','network.floating','cloudstorage','instance.addon','tenant.addon']
            services_mapping = OrderedDict()

            # Mapping for a services
            services_mapping = {'compute': 'Compute', 'image': 'Image','volume': 'Block Storage (Volume)', 'network.bw.in': 'Network Transfer (inbound)', 'network.bw.out': 'Network Transfer (outbound)', 'network.floating': 'Floating IP Addresses', 'cloudstorage': 'Object Storage (Swift)', 'instance.addon': 'Compute Instance Add-On', 'tenant.addon': 'Project Add-On' }

            now = datetime.datetime.now() 
            start_time_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
            start_date_week = now - dateutil.relativedelta.relativedelta(days=7)
            start_date_week = start_date_week.replace(hour=0, minute=0, second=0, microsecond=0)
            start_date_month = now - dateutil.relativedelta.relativedelta(months=1)
            start_date_month = start_date_month.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Add data to the context here...
            total = api.cloudkittyclient(request).reports.get_total(
                    tenant_id=request.user.tenant_id, begin=start_time_today, end= now) or 0.00
    
            total_dict = {}
            total_dict = OrderedDict(total_dict)
            for service_items in services:
                    totals = api.cloudkittyclient(request).reports.get_total(
                            tenant_id=request.user.tenant_id, service=service_items, begin=start_time_today, end= now) or 0.00
                    service_items = services_mapping[service_items]
                    total_dict[service_items] = totals
    
            total_week = api.cloudkittyclient(request).reports.get_total(
                    tenant_id=request.user.tenant_id, begin=start_date_week, end= now) or 0.00
    
            total_week_dict = {}
            total_week_dict = OrderedDict(total_week_dict)
            for service_items in services:
                    totals_week = api.cloudkittyclient(request).reports.get_total(
                            tenant_id=request.user.tenant_id, service=service_items, begin=start_date_week, end= now) or 0.00
                    service_items = services_mapping[service_items]
                    total_week_dict[service_items] = totals_week
    
            total_month = api.cloudkittyclient(request).reports.get_total(
                    tenant_id=request.user.tenant_id, begin=start_date_month, end=now) or 0.00
    
            total_month_dict = {}
            total_month_dict = OrderedDict(total_month_dict)
            for service_items in services:
                    totals_month = api.cloudkittyclient(request).reports.get_total(
                            tenant_id=request.user.tenant_id, service=service_items, begin=start_date_month, end= now) or 0.00
                    service_items = services_mapping[service_items]
                    total_month_dict[service_items] = totals_month
    
            # cloud resource section
            total_cloud = api.cloudkittyclient(request).reports.get_total(
                    tenant_id=request.user.tenant_id, begin=start_period_cloud, end=now) or 0.00

            # cloud resources section    
            total_cloud_dict = {}
            total_cloud_dict = OrderedDict(total_cloud_dict)
            for service_items in services:
                    totals_cloud = api.cloudkittyclient(request).reports.get_total(
                            tenant_id=request.user.tenant_id, service=service_items, begin=start_period_cloud, end=now) or 0.00
                    service_items = services_mapping[service_items]
                    total_cloud_dict[service_items] = totals_cloud
       
        context['total_today'] = total
        context['start_period_today'] = start_time_today.strftime('%b %d %Y %H:%M')
        context['end_period'] = now.strftime('%b %d %Y %H:%M')
        context['total_dict'] = total_dict

        context['total_week'] = total_week
        context['start_period_week'] = start_date_week.strftime('%b %d %Y %H:%M')
        context['end_period'] = now.strftime('%b %d %Y %H:%M')
        context['total_week_dict'] = total_week_dict

        context['total_month'] = total_month
        context['start_period_month'] = start_date_month.strftime('%b %d %Y %H:%M')
        context['end_period'] = now.strftime('%b %d %Y %H:%M')
        context['total_month_dict'] = total_month_dict

        context['total_cloud'] = total_cloud
        context['start_period_cloud'] = start_period_cloud.strftime('%b %d %Y %H:%M')
        context['end_period'] = now.strftime('%b %d %Y %H:%M')
	context['total_cloud_dict'] = total_cloud_dict

        return context

    # convert the local time to UTC
    def local2utc(self, dt):

        tenant_timezone = self.tenant_timezone
        from_zone = tz.gettz(tenant_timezone)
        to_zone = tz.gettz('UTC')
        local = dt.replace(tzinfo=from_zone)
        return local.astimezone(to_zone).replace(tzinfo = None)

def quote(request):
    pricing = "0"
    if request.is_ajax():
        if request.method == 'POST':
            json_data = json.loads(request.body)
            try:
                pricing = decimal.Decimal(api.cloudkittyclient(request)
                                          .quotations.quote(json_data))
                pricing = pricing.normalize().to_eng_string()
            except Exception:
                exceptions.handle(request,
                                  _('Unable to retrieve price.'))

    return http.HttpResponse(json.dumps(pricing),
                             content_type='application/json')
