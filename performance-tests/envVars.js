export const baseUrls = {
  auth: 'https://api-mcshared.uat.cstar.pagopa.it',
  sender: 'https://api-rtp.uat.cstar.pagopa.it',
};

export const auth = {
  getToken: '/auth/token',
};

export const sender = {
  sendRTP: '/rtp/rtps',
};

export const serviceRegistry = {
  getEnti: '/rtp/payees/payees',
  getServiceProvides: ''
};

export const secrets = {
  clientId: __ENV.CLIENT_ID,
  clientSecret: __ENV.CLIENT_SECRET,
  serviceProviderId: __ENV.SERVICE_PROVIDER_ID
};

