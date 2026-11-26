const assert = require('node:assert/strict');
const { readFile } = require('node:fs/promises');
const { resolve } = require('node:path');
const test = require('node:test');
const {
  assertFails,
  assertSucceeds,
  initializeTestEnvironment,
} = require('@firebase/rules-unit-testing');
const {
  deleteDoc,
  doc,
  getDoc,
  setDoc,
  updateDoc,
} = require('firebase/firestore');

const projectId = 'ai-resume-ranking-system';
const candidateId = 'candidate-1';
const otherCandidateId = 'candidate-2';
const recruiterId = 'recruiter-1';
const applicationId = 'application-1';

const applicationData = {
  jobId: 'job-1',
  jobTitle: 'Flutter Developer',
  companyName: 'Example Co',
  recruiterId,
  candidateId,
  candidateEmail: 'candidate@example.com',
  candidateName: 'Candidate One',
  resumeFileName: 'resume.pdf',
  resumeStoragePath: 'private/resume.pdf',
  appliedAt: '2026-11-06T00:00:00.000Z',
  status: 'Pending',
  score: 40,
  scoreBreakdown: {
    skillsScore: 20,
    experienceScore: 25,
    educationScore: 20,
    practicalWorkScore: 14,
    finalScore: 79,
  },
  scoringStatus: 'scored',
  scoringModelVersion: 3,
  scoreShared: false,
};

const projectionData = {
  jobId: 'job-1',
  jobTitle: 'Flutter Developer',
  recruiterId,
  candidateId,
  candidateName: 'Candidate One',
  resumeFileName: 'resume.pdf',
  appliedAt: '2026-11-06T00:00:00.000Z',
  status: 'Pending',
  scoreShared: false,
};

let testEnv;

async function seed() {
  await testEnv.withSecurityRulesDisabled(async (context) => {
    const db = context.firestore();
    await setDoc(doc(db, `jobs/job-1`), {
      createdBy: recruiterId,
      status: 'active',
    });
    await setDoc(doc(db, `applications/${applicationId}`), applicationData);
    await setDoc(
      doc(db, `candidateApplications/${applicationId}`),
      projectionData,
    );
    await setDoc(doc(db, 'candidateApplications/application-2'), {
      ...projectionData,
      candidateId: otherCandidateId,
      candidateName: 'Candidate Two',
    });
    await setDoc(doc(db, 'applications/application-3'), {
      ...applicationData,
      candidateId,
    });
    await setDoc(doc(db, 'candidateApplications/application-3'), {
      ...projectionData,
    });
  });
}

function candidateDb(uid = candidateId) {
  return testEnv.authenticatedContext(uid).firestore();
}

function recruiterDb() {
  return testEnv.authenticatedContext(recruiterId).firestore();
}

test.before(async () => {
  const rules = await readFile(
    resolve(process.cwd(), '..', 'firestore.rules'),
    'utf8',
  );
  testEnv = await initializeTestEnvironment({
    projectId,
    firestore: { rules },
  });
  await seed();
});

test.after(async () => {
  await testEnv.cleanup();
});

test('candidate cannot directly create private application or projection', async () => {
  const db = candidateDb();
  await assertFails(
    setDoc(doc(db, 'applications/client-created-application'), {
      ...applicationData,
      candidateId,
    }),
  );
  await assertFails(
    setDoc(doc(db, 'candidateApplications/client-created-application'), {
      ...projectionData,
      candidateId,
    }),
  );
});

test('candidate cannot read recruiter score or breakdown', async () => {
  await assertFails(getDoc(doc(candidateDb(), `applications/${applicationId}`)));
});

test('candidate cannot read another candidate projection', async () => {
  await assertFails(
    getDoc(doc(candidateDb(), 'candidateApplications/application-2')),
  );
});

test('candidate cannot forge status, score sharing, or private fields', async () => {
  const db = candidateDb();
  await assertFails(
    updateDoc(doc(db, `candidateApplications/${applicationId}`), {
      status: 'Rejected',
    }),
  );
  await assertFails(
    updateDoc(doc(db, `candidateApplications/${applicationId}`), {
      scoreShared: true,
      score: 79,
    }),
  );
  await assertFails(
    setDoc(doc(db, 'candidateApplications/forged'), {
      ...projectionData,
      status: 'Rejected',
      scoreShared: true,
      scoreBreakdown: { finalScore: 100 },
    }),
  );
});

test('candidate cannot create a projection with forged initial fields', async () => {
  const db = candidateDb();
  await assertFails(
    setDoc(doc(db, 'candidateApplications/forged-status'), {
      ...projectionData,
      status: 'Rejected',
    }),
  );
});

test('authorized HR can read scores and perform recruitment actions', async () => {
  const db = recruiterDb();
  await assertSucceeds(getDoc(doc(db, `applications/${applicationId}`)));
  await assertSucceeds(
    updateDoc(doc(db, `applications/${applicationId}`), {
      status: 'Rejected',
    }),
  );
  await assertSucceeds(
    updateDoc(doc(db, `applications/${applicationId}`), {
      scoreShared: true,
    }),
  );
  await assertSucceeds(
    updateDoc(doc(db, `candidateApplications/${applicationId}`), {
      status: 'Rejected',
      scoreShared: false,
    }),
  );
});

test('candidate projection remains score-free and recruiter cannot write score fields', async () => {
  const recruiter = recruiterDb();
  const candidate = candidateDb();
  const projection = await getDoc(
    doc(candidate, 'candidateApplications/application-3'),
  );
  assert.equal(projection.data().status, 'Pending');
  assert.equal(projection.data().scoreShared, false);
  assert.equal('score' in projection.data(), false);
  assert.equal('scoreBreakdown' in projection.data(), false);
  await assertFails(
    updateDoc(doc(recruiter, 'candidateApplications/application-3'), {
      score: applicationData.score,
    }),
  );
  await assertFails(
    updateDoc(doc(recruiter, 'candidateApplications/application-3'), {
      scoreBreakdown: applicationData.scoreBreakdown,
    }),
  );
});

test('candidate score document is denied before sharing', async () => {
  await assertFails(
    getDoc(doc(candidateDb(), 'candidateApplicationScores/application-3')),
  );
});

test('candidate can read shared score without changing application status', async () => {
  const recruiter = recruiterDb();
  const candidate = candidateDb();
  await testEnv.withSecurityRulesDisabled(async (context) => {
    const db = context.firestore();
    await updateDoc(doc(db, 'applications/application-3'), {
      scoreShared: true,
    });
    await setDoc(doc(db, 'candidateApplicationScores/application-3'), {
      score: applicationData.score,
      scoreBreakdown: applicationData.scoreBreakdown,
    });
  });
  const score = await getDoc(
    doc(candidate, 'candidateApplicationScores/application-3'),
  );
  assert.equal(score.data().score, applicationData.score);
  assert.deepEqual(
    score.data().scoreBreakdown,
    applicationData.scoreBreakdown,
  );
  const application = await getDoc(
    doc(recruiter, 'applications/application-3'),
  );
  assert.equal(application.data().status, 'Pending');
});

test('candidates cannot access another candidate score document', async () => {
  await assertFails(
    getDoc(
      doc(candidateDb(otherCandidateId), 'candidateApplicationScores/application-3'),
    ),
  );
});

test('clients cannot create, update, or delete candidate score documents', async () => {
  const candidate = candidateDb();
  const recruiter = recruiterDb();
  const scoreDocument = doc(candidate, 'candidateApplicationScores/application-3');
  await assertFails(
    setDoc(scoreDocument, { score: 79 }),
  );
  await assertFails(
    updateDoc(scoreDocument, { score: 80 }),
  );
  await assertFails(
    updateDoc(scoreDocument, {
      scoreBreakdown: applicationData.scoreBreakdown,
      scoreShared: true,
    }),
  );
  await assertFails(
    updateDoc(doc(recruiter, 'candidateApplicationScores/application-3'), {
      score: 80,
    }),
  );
  await assertFails(
    setDoc(
      doc(recruiter, 'candidateApplicationScores/new-score'),
      { score: 79 },
    ),
  );
  await assertFails(
    updateDoc(
      doc(recruiter, 'candidateApplicationScores/application-3'),
      { scoreBreakdown: applicationData.scoreBreakdown },
    ),
  );
  await assertFails(
    deleteDoc(
      doc(recruiter, 'candidateApplicationScores/application-3'),
    ),
  );
  await assertFails(
    deleteDoc(doc(candidate, 'candidateApplicationScores/application-3')),
  );
});

test('shared rejection score is visible only to the intended candidate', async () => {
  await assertSucceeds(
    getDoc(doc(candidateDb(), `candidateApplications/${applicationId}`)),
  );
  await assertFails(
    getDoc(doc(candidateDb(otherCandidateId), `candidateApplications/${applicationId}`)),
  );
});

test('HR cannot overwrite scoring fields through client rules', async () => {
  await assertFails(
    updateDoc(doc(recruiterDb(), `applications/${applicationId}`), {
      score: 79,
      scoreBreakdown: applicationData.scoreBreakdown,
    }),
  );
});
