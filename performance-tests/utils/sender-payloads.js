import {randomNoticeNumber, replaceUuidWithoutDashes} from "./utils.js";

/**
 * Build the payload JSON for sending an RTP (Request To Pay).
 * @param {string} payerId - Identifier of the payer (e.g., SERVICE_PROVIDER_ID).
 * @returns {Object}
 */
export function buildSendPayload(payerId) {
    const noticeNumber = randomNoticeNumber();
    return {
        payee: {
            name: 'Comune di Smartino',
            payeeId: '77777777777',
            payTrxRef: 'ABC/124',
        },
        payer: {
            name: 'Pigrolo',
            payerId,
        },
        paymentNotice: {
            noticeNumber,
            description: 'Paga questo avviso',
            subject: 'TARI 2025',
            amount: 40000,
            expiryDate: '2025-12-31',
        },
    };
}

/**
 * Build the payload JSON to simulate the callback response (ACTC) for a sent RTP.
 * @param {string} resourceId - RTP UUID (with dashes).
 * @returns {Object}
 */
export function buildCallbackPayload(resourceId) {
    const resourceIdNoDash = replaceUuidWithoutDashes(resourceId);
    const nowIso = new Date().toISOString();

    return {
        resourceId: '71f18650-6025-477e-91b9-a65c212176f0',
        AsynchronousSepaRequestToPayResponse: {
            resourceId: '71f18650-6025-477e-91b9-a65c212176f0',
            Document: {
                CdtrPmtActvtnReqStsRpt: {
                    GrpHdr: {
                        CreDtTm: nowIso,
                        InitgPty: {
                            Id: {OrgId: {AnyBIC: 'MOCKSP04'}}
                        },
                        MsgId: resourceIdNoDash
                    },
                    OrgnlGrpInfAndSts: {
                        OrgnlCreDtTm: nowIso,
                        OrgnlMsgId: resourceIdNoDash,
                        OrgnlMsgNmId: 'pain.013.001.07'
                    },
                    OrgnlPmtInfAndSts: [
                        {
                            OrgnlPmtInfId: '302001233424245781',
                            TxInfAndSts: [
                                {
                                    OrgnlEndToEndId: '302001233424245781',
                                    OrgnlInstrId: '0016f716c17440ed91c7888f08ad1f6a',
                                    OrgnlTxRef: {
                                        Amt: {InstdAmt: 120},
                                        Cdtr: {Id: {OrgId: {}}, Nm: 'EC MOCK'},
                                        CdtrAcct: {Id: {IBAN: 'IT96K999999999900SRTPPAGOPA'}},
                                        CdtrAgt: {
                                            FinInstnId: {
                                                Othr: {Id: '15376371009', SchmeNm: {Cd: 'BOID'}}
                                            }
                                        },
                                        DbtrAgt: {FinInstnId: {BICFI: ''}},
                                        PmtTpInf: {
                                            LclInstrm: {Prtry: 'PAGOPA'},
                                            SvcLvl: [{Cd: 'SRTP'}]
                                        },
                                        ReqdExctnDt: {Dt: '2025-06-30Z'},
                                        XpryDt: {Dt: '2025-06-30Z'}
                                    },
                                    StsId: resourceIdNoDash,
                                    StsRsnInf: [
                                        {Orgtr: {Id: {OrgId: {AnyBIC: ''}}}}
                                    ],
                                    TxSts: 'ACTC'
                                }
                            ]
                        }
                    ]
                }
            }
        }
    };
}
