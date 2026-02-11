//MONTHEND  JOB (ACCT),'MONTHEND',CLASS=A,MSGCLASS=H,NOTIFY=&SYSUID
//*
//* IWS will submit this JOB via schedule; no parameters required.
//*
//STEP1     EXEC PGM=MONTHEND
//* If needed, uncomment STEPLIB:
//*STEPLIB  DD  DISP=SHR,DSN=YOUR.COBOL.LOADLIB
//SYSOUT    DD  SYSOUT=*
//SYSPRINT  DD  SYSOUT=*
//SYSUDUMP  DD  SYSOUT=*
//CEEDUMP   DD  SYSOUT=*
//*
//* Input/output files (hardcoded in COBOL -> must map to DDNAMEs)
//* Replace DSNs to your environment.
//CUSTOMERS DD  DISP=SHR,DSN=YOUR.APP.CUSTOMERS.DAT
//TRANSFILE DD  DISP=SHR,DSN=YOUR.APP.TRANSACTIONS.DAT
