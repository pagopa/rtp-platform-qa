import {addDays, generateNumericString, randomNoticeNumber, replaceUuidWithoutDashes} from "./utils.js";

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

/**
 * Builds a GPD message payload used for stress test executions.
 *
 * This helper is designed for performance testing scenarios and produces
 * synthetic, non-production data.
 *
 * @example
 * const payload = buildGpdMessagePayload(
 *   "RSSMRA80A01H501U",      // debtorFiscalCode
 *   generatePositiveLong(), // operationId
 *   "CREATE",               // operation
 *   "VALID",                // status
 *   "80015010723",          // ecTaxCode
 *   "12345678901"           // optional pspTaxCode
 * );
 *
 * @param {string} debtorFiscalCode
 *  Fiscal code of the debtor. Mapped to `debtor_tax_code` in the payload.
 *
 * @param {number|string} operationId
 *  Unique identifier of the operation. Used as the `id` field and typically
 *  generated per request to ensure idempotency during stress tests.
 *
 * @param {string} operation
 *  Type of operation to be simulated (e.g. "CREATE", "UPDATE", "DELETE").
 *
 * @param {string} status
 *  Business status of the message (e.g. "VALID").
 *
 * @param {string} ecTaxCode
 *  Creditor entity tax code.
 *
 * @param {string} [psp_tax_code]
 *  Optional PSP tax code. If not provided, the value defaults to null.
 *
 * @returns {Object}
 *  Fully constructed GPD message payload ready to be serialized and sent.
 */

export function buildGpdMessagePayload(
    debtorFiscalCode,
    operationId,
    operation,
    status,
    ecTaxCode,
    psp_tax_code) {

    const timestamp = Date.now();
    const iuv = generateNumericString(17);
    const dueDate = addDays(timestamp, 30);
    const nav = generateNumericString(18);

    return {
        "id": operationId,
        "operation": operation,
        "timestamp": timestamp,
        "iuv": iuv,
        "subject": "GPD Stress Test Remittance",
        "description": "Automated stress test message - non production data",
        "ec_tax_code": ecTaxCode,
        "debtor_tax_code": debtorFiscalCode,
        "nav": nav,
        "due_date": dueDate,
        "amount": 30000,
        "status": status,
        "psp_code": null,
        "psp_tax_code": psp_tax_code ?? null
    }
}
