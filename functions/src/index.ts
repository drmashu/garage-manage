// ////////////////////////////////////////////////////////////////////////////
// Garage Manage Cloud Functions定義
// ////////////////////////////////////////////////////////////////////////////

import * as functions from "firebase-functions";
import * as admin from "firebase-admin";

admin.initializeApp(functions.config().firebase);
const store = admin.firestore();

// ////////////////////////////////////////////////////////////////////////////
// Picoの操作
// ////////////////////////////////////////////////////////////////////////////
export const pico =
functions.region("asia-northeast1").https.onCall(async (data, context) => {
  functions.logger.info("start pico");
  if (!context.auth) {
    throw new functions.https.HttpsError("unauthenticated", "auth error");
  }
  functions.logger.info("data : " + JSON.stringify(data));
  functions.logger.info("context : " + JSON.stringify(context));
  const {picoId, shutter, light, fan} = data;
  const {rawRequest} = context;
  functions.logger.info("update pico id : " + picoId);
  const docRef = store.collection("picos").doc(picoId);

  const doc = await docRef.get();
  let bottom = Number(doc.get("bottom"));
  bottom = bottom < shutter ? shutter : bottom;
  let top = Number(doc.get("top"));
  top = top > shutter ? shutter : top;
  const present = (shutter - top) / (bottom - top) * 100;

  docRef.update({
    "top": top,
    "bottom": bottom,
    "present": present,
    "light": light,
    "fan": fan,
    "ip": rawRequest.ip,
  });
  return {response: "OK"};
});

export const shutter =
functions.region("asia-northeast1").https.onCall(async (data, context) => {
  functions.logger.info("start manage");
  if (!context.auth) {
    throw new functions.https.HttpsError("unauthenticated", "auth error");
  }
});
