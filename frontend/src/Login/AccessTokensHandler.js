import React from 'react';

// Backbone
import AccessTokenCollection from '../Backbone/Collections/AccessToken'

import AccessTokens from './AccessTokens'

class AccessTokensHandler extends React.Component
{
	render()
	{
		return (
			<div>
				<AccessTokens type={AccessTokenCollection} />
			</div>
		);
	}
}

module.exports = AccessTokensHandler;