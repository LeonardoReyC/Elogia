/** @odoo-module **/

import {registerModel, registerPatch} from '@mail/model/model_core';
import {attr, many, one} from '@mail/model/model_field';

import {sprintf} from '@web/core/utils/strings';

registerPatch({
    name: 'SuggestedRecipientInfo',
    fields: {

        isSelected: {
            /**
             * Prevents selecting a recipient that does not have a partner.
             */
            compute() {
                return false;
            },
        },

    },
});