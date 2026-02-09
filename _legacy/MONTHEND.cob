       IDENTIFICATION DIVISION.
       PROGRAM-ID. MONTHEND.
       AUTHOR. BANKING-SYSTEM.
       DATE-WRITTEN. 2026-02-09.

       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT CUSTOMER-FILE ASSIGN TO 'CUSTOMERS.DAT'
               ORGANIZATION IS LINE SEQUENTIAL
               FILE STATUS IS C-FILE-STATUS.
           SELECT TRANSACTION-FILE ASSIGN TO 'TRANSACTIONS.DAT'
               ORGANIZATION IS LINE SEQUENTIAL
               FILE STATUS IS T-FILE-STATUS.

       DATA DIVISION.
       FILE SECTION.
       FD CUSTOMER-FILE.
       01 CUSTOMER-RECORD.
           05 ACCT-ID     PIC X(10).
           05 NAME        PIC X(30).
           05 BALANCE     PIC 9(7)V99.
           05 ACCT-TYPE   PIC X(1).

       FD TRANSACTION-FILE.
       01 TRANSACTION-RECORD.
           05 TRANS-ACCT-ID    PIC X(10).
           05 TRANS-TYPE       PIC X(1).
           05 TRANS-AMOUNT     PIC 9(7)V99.
           05 TRANS-DATE       PIC X(10).
           05 TRANS-TIME       PIC X(8).

       WORKING-STORAGE SECTION.
       01 C-FILE-STATUS    PIC XX.
       01 T-FILE-STATUS    PIC XX.

       01 WS-SEARCH-ID     PIC X(10).
       01 WS-AMOUNT        PIC 9(7)V99.
       01 WS-COUNT-UPDATED PIC 9(5) VALUE 0.

       01 WS-CURRENT-DATE.
           05 WS-YEAR      PIC 9999.
           05 WS-MONTH     PIC 99.
           05 WS-DAY       PIC 99.
       01 WS-CURRENT-TIME.
           05 WS-HOUR      PIC 99.
           05 WS-MINUTE    PIC 99.
           05 WS-SECOND    PIC 99.
       01 WS-DATE-STRING   PIC X(10).
       01 WS-TIME-STRING   PIC X(8).

       PROCEDURE DIVISION.
       MAIN-PARA.
           DISPLAY "MONTHEND INTEREST BATCH START"
           DISPLAY "Applying 2% annual interest to all savings accounts..."

           OPEN I-O CUSTOMER-FILE
           IF C-FILE-STATUS NOT = "00"
               DISPLAY "Error opening customer file: " C-FILE-STATUS
               GO TO END-PROGRAM
           END-IF

           PERFORM UNTIL C-FILE-STATUS = "10"
               READ CUSTOMER-FILE
               IF C-FILE-STATUS = "00"
                   IF ACCT-TYPE = 'S'
                       COMPUTE WS-AMOUNT = BALANCE * 0.02
                       ADD WS-AMOUNT TO BALANCE
                       REWRITE CUSTOMER-RECORD
                       ADD 1 TO WS-COUNT-UPDATED
                       MOVE ACCT-ID TO WS-SEARCH-ID
                       PERFORM LOG-TRANSACTION-INTEREST
                   END-IF
               END-IF
           END-PERFORM

           CLOSE CUSTOMER-FILE

           DISPLAY "Interest applied to " WS-COUNT-UPDATED " savings accounts."
           DISPLAY "MONTHEND INTEREST BATCH COMPLETE"

           STOP RUN.

       LOG-TRANSACTION-INTEREST.
           PERFORM GET-CURRENT-DATETIME
           OPEN EXTEND TRANSACTION-FILE
           IF T-FILE-STATUS NOT = "00"
               DISPLAY "Error opening transaction file: " T-FILE-STATUS
           ELSE
               MOVE WS-SEARCH-ID TO TRANS-ACCT-ID
               MOVE 'I' TO TRANS-TYPE
               MOVE WS-AMOUNT TO TRANS-AMOUNT
               MOVE WS-DATE-STRING TO TRANS-DATE
               MOVE WS-TIME-STRING TO TRANS-TIME
               WRITE TRANSACTION-RECORD
           END-IF
           CLOSE TRANSACTION-FILE.

       GET-CURRENT-DATETIME.
           ACCEPT WS-CURRENT-DATE FROM DATE YYYYMMDD
           ACCEPT WS-CURRENT-TIME FROM TIME
           STRING WS-YEAR '/' WS-MONTH '/' WS-DAY DELIMITED BY SIZE
               INTO WS-DATE-STRING
           STRING WS-HOUR ':' WS-MINUTE ':' WS-SECOND DELIMITED BY SIZE
               INTO WS-TIME-STRING.

       END-PROGRAM.
           STOP RUN.
