package test.networkpolicy

deny[msg] {
  input.kind == "NetworkPolicy"
  false  
}

