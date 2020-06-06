#lang racket

;; i feel good or alright about these
(define (indent str)
  (define lines (string-split str "\n"))
  (string-join
   (map
    (lambda (line) (string-append "\t" line))
    lines)
   "\n"))

(define (cpp-scope expr)
  (format "{~n~a~n}" (indent expr)))

(define (cpp-block head body foot)
  (format "~a~n~a~a~n" head (cpp-scope body) foot))

(define (cpp-namespace spacename expr)
  (cpp-block (format "namespace ~a" spacename) expr ""))


(define (cpp-struct name . members)
  (cpp-block
   (format "struct ~a" name)
   (string-join
     members
     "\n")
   ";\n"))


;; these need work
(define (cpp-fn-signature return-type fn-name . args)
  (format
   "~a ~a(~a)"
   return-type
   fn-name
   (string-join (map ~a args) ", ")))


;; test
(display
 (cpp-namespace
  "fnord"
  (cpp-struct "hail_eris" "a" "b" "c" "d")))
