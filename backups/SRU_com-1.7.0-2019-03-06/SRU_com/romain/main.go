package main

import (
	"bufio"
	"encoding/hex"
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"os"
	"strconv"
	"time"

	"github.com/fatih/color"
	"github.com/tarm/serial"
)

//FlagClearWDG = Flag pour UART RX
var FlagClearWDG byte = 0x00

//BDstruct = Structure de la BD
type BDstruct struct {
	Name   string     `json:"name"`
	Header string     `json:"header"`
	Length string     `json:"length"`
	Tag    string     `json:"tag"`
	Data   [][]string `json:"data"`
}

//ListeTC variable globale
var ListeTC []BDstruct

//IndexationTC idex TAG<->Indice
var IndexationTC [256]int

//ListeTM variable globale
var ListeTM []BDstruct

//IndexationTM idex TAG<->Indice
var IndexationTM [256]int

//RxUART thread pour le TX
func RxUART(s *serial.Port) {
	b := make([]byte, 2048)
	buf := make([]byte, 64)
	/*var i int
	var TmBoot byte
	var TmAppli byte
	var SizeTm int*/
	var NumberRead int
	//var FlagQuit byte
	var LenData byte
	var Tag byte
	var Crc byte
	//var NbrChampData int
	//var NbrOctetData int
	var counter int
	var counterResidu int
	var LenFrame int
	var ResiduUart int
	var count int

	file, _ := os.Create("DUMP_Appli_MRAM.txt")

	defer file.Close()

	ResiduUart = 0

	for {
		counter = 0
		LenFrame = -1
		for counter != LenFrame {
			a := make([]byte, 2048)
			if ResiduUart != 0 {
				NumberRead = ResiduUart
				//fmt.Printf("\nResidu: %d ", ResiduUart)
				copy(a, b)
			} else {
				NumberRead, _ = s.Read(a)
				//fmt.Printf("\nStart UART : %d ", NumberRead)
				//fmt.Printf("Trame Uart : %x\n", a[:NumberRead])
			}
			ResiduUart = 0

			//fmt.Printf("Counter = %d\n", counter)
			for x := 0; x < NumberRead; x++ {
				if counter == 0 {
					if a[x] == 0x12 || a[x] == 0x43 {
						buf[0] = a[x]
						//fmt.Printf("H1 : 0x%02X ", buf[0])
						counter++
					} else {
						counter = 0
					}
				} else if counter == 1 {
					if buf[0] == 0x12 {
						if a[x] == 0x43 {
							buf[1] = a[x]
							counter++
						} else if a[x] == 0x12 {
							buf[0] = a[x]
							counter = 1
						} else {
							counter = 0
						}
					} else if buf[0] == 0x43 {
						if a[x] == 0x12 {
							buf[1] = a[x]
							counter++
						} else if a[x] == 0x43 {
							buf[0] = a[x]
							counter = 1
						} else {
							counter = 0
						}
					} else {
						counter = 0
					}
				} else if counter == 2 {
					buf[2] = a[x]
					LenData = a[x]
					LenFrame = int(a[x]) + 5
					counter++
				} else if counter == 3 {
					buf[3] = a[x]
					Tag = buf[3]
					counter++
				} else if counter > 3 && counter < LenFrame-1 {
					buf[counter] = a[x]
					counter++
				} else if counter == LenFrame-1 {
					buf[counter] = a[x]
					Crc = buf[counter]
					_ = Crc
					counter++
				}
				if ResiduUart != 0 {
					ResiduUart--
				} else {
					counterResidu = 0
				}

				if counter == LenFrame {
					count++
					if x < NumberRead-1 {
						counterResidu += counter
						ResiduUart = NumberRead - 1 - x
						copy(b, a[counterResidu:NumberRead])
						counter = 0
					} else {
						ResiduUart = 0
						counterResidu = 0
						counter = 0
					}

					if buf[1] == 0x43 {
						NewTM := color.New(color.FgHiRed, color.Bold)
						NewTM.EnableColor()
						NewTM.Printf("\n - TM Appl : %s - :", ListeTM[IndexationTM[Tag]].Name)
					} else {
						NewTM := color.New(color.FgHiRed, color.Bold)
						NewTM.EnableColor()
						NewTM.Printf("\n - TM Boot : %s - :", ListeTM[IndexationTM[Tag]].Name)
					}

					HeaderColor := color.New(color.FgHiMagenta)
					LenColor := color.New(color.FgHiYellow)
					TagColor := color.New(color.FgHiBlue)
					DataRawColor := color.New(color.FgHiGreen)
					CRCColor := color.New(color.FgHiRed)

					HeaderColor.EnableColor()
					LenColor.EnableColor()
					TagColor.EnableColor()
					DataRawColor.EnableColor()
					CRCColor.EnableColor()
					if ListeTM[IndexationTM[Tag]].Tag == "0E" {
						fmt.Fprintf(file, ":")
					}

					for h := 0; h < LenFrame; h++ {
						if h < 2 {
							HeaderColor.Printf(" 0x%02X", buf[h])
						} else if h == 2 {
							LenColor.Printf(" 0x%02X", buf[h])
						} else if h == 3 {
							TagColor.Printf(" 0x%02X", buf[h])
						} else if h > 3 && h != LenFrame-1 {
							DataRawColor.Printf(" 0x%02X", buf[h])
							if ListeTM[IndexationTM[Tag]].Tag == "0E" {
								fmt.Fprintf(file, "%02X", buf[h])
							}
						} else {
							CRCColor.Printf(" 0x%02X", buf[h])
						}
					}
					if ListeTM[IndexationTM[Tag]].Tag == "0E" {
						fmt.Fprintf(file, "\n")
					}
					fmt.Printf("\n\n")

					fmt.Printf("\tSynchro 1 :")
					HeaderColor.Printf(" 0x%02x\n", buf[0])
					fmt.Printf("\tSynchro 2 :")
					HeaderColor.Printf(" 0x%02x\n", buf[1])

					fmt.Printf("\tData Len  :")
					LenColor.Printf(" 0x%02x (%03d)\n", buf[2], int(buf[2]))

					fmt.Printf("\tTAG       :")
					TagColor.Printf(" 0x%02x\n\n", buf[3])

					if LenData != 0 {
						var count int
						count = 0
						_ = count

						var MaxSize int

						for b := 0; b < len(ListeTM[IndexationTM[Tag]].Data); b++ {
							if MaxSize < len(ListeTM[IndexationTM[Tag]].Data[b][1]) {
								MaxSize = len(ListeTM[IndexationTM[Tag]].Data[b][1])
							}
						}

						for y := 0; y < len(ListeTM[IndexationTM[Tag]].Data); y++ {
							fmt.Printf("\t%s ", ListeTM[IndexationTM[Tag]].Data[y][1])
							LenDecom := int(S2H(ListeTM[IndexationTM[Tag]].Data[y][0]))

							for i := 0; i < LenDecom; i++ {
								if i == 0 {
									for w := 0; w < MaxSize-(len(ListeTM[IndexationTM[Tag]].Data[y][1])); w++ {
										fmt.Printf(" ")

									}
									fmt.Printf(": ")
								}
								if LenDecom == 1 {
									DataRawColor.Printf("0x%02x (%03d)", buf[4+count], int(buf[4+count]))
								} else {
									DataRawColor.Printf("0x%02x ", buf[4+count])
								}
								count++
							}

							fmt.Printf("\n")
						}
						fmt.Printf("\n")
					}
					fmt.Printf("\tCRC       :")
					CRCColor.Printf(" 0x%02x\n\n", buf[LenData+4])
				}

			}
		}
	}
}

//ComputeCRCDUMP calcule le CRC du fichier DUMP_Appli_MRAM.txt
func ComputeCRCDUMP() {
	file, err1 := os.Open("DUMP_Appli_MRAM.txt")
	if err1 != nil {
		log.Fatal(err1)
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)

	var LineHex string
	var ByteLineHex [128]byte
	var crcPoly byte
	var crc byte
	var data byte
	var counter byte

	counter = 0
	data = 0x00
	crc = 0x00
	crcPoly = 0xD5

	for scanner.Scan() {
		LineHex = ""
		LineHex = scanner.Text()
		if len(LineHex) != 0 {
			if LineHex[0] == ':' {
				//fmt.Printf("%s\n", LineHex)
				for i := 0; i < ((len(LineHex) - 1) / 2); i++ {
					ByteLineHex[i] = byte(S2H(LineHex[1+(2*i) : 1+(2*i)+2]))
					//fmt.Printf("\n%x", ByteLineHex[i])
				}

				//fmt.Printf("Len : %02d  Addr : 0x%04x\n", ByteLineHex[0], LastAddr)
				for i := 0; i < 16; i++ {
					data = ByteLineHex[2+i]
					//fmt.Printf("%d : 0x%02x    ", i, data)
					for counter = 0; counter < 0x08; counter++ {
						if (data&0x80)^(crc&0x80) != 0x00 {
							crc = ((crc << 1) ^ crcPoly)
						} else {
							crc = (crc << 1)
						}
						data = data << 1
					}

				}
			}
		}
	}
	CRCColor := color.New(color.FgGreen)
	CRCColor.EnableColor()
	fmt.Printf("\n\tCRC DUMP file : ")
	CRCColor.Printf("0x%02X\n", crc)
}

//ComputeCRCHEX calcule le CRC du fichier .hex
func ComputeCRCHEX() {
	file, err1 := os.Open("main.hex")
	if err1 != nil {
		log.Fatal(err1)
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)

	var LineHex string
	var ByteLineHex [128]byte
	var crcPoly byte
	var crc byte
	var data byte
	var counter byte
	var x int16
	var LastLen int
	var LastAddr int16

	counter = 0
	data = 0x00
	crc = 0x00
	crcPoly = 0xD5
	LastAddr = 0
	LastLen = 0

	for scanner.Scan() {
		LineHex = ""
		LineHex = scanner.Text()
		if len(LineHex) != 0 {
			if LineHex[0] == ':' {
				//fmt.Printf("%s\n", LineHex)
				for i := 0; i < ((len(LineHex) - 1) / 2); i++ {
					ByteLineHex[i] = byte(S2H(LineHex[1+(2*i) : 1+(2*i)+2]))
					//fmt.Printf("\n%x", ByteLineHex[i])
				}
				if ByteLineHex[3] == 0x00 {
					LastAddr = int16(ByteLineHex[2]) + (int16(ByteLineHex[1]) << 8)
					//fmt.Printf("Len : %02d  Addr : 0x%04x\n", ByteLineHex[0], LastAddr)
					LastLen = int(ByteLineHex[0])
					for i := 0; i < LastLen; i++ {
						data = ByteLineHex[4+i]
						//fmt.Printf("%d : 0x%02x    ", i, data)
						for counter = 0; counter < 0x08; counter++ {
							if (data&0x80)^(crc&0x80) != 0x00 {
								crc = ((crc << 1) ^ crcPoly)
							} else {
								crc = (crc << 1)
							}
							data = data << 1
						}
						//fmt.Printf("0x%02x ", crc)
					}
				}
			}
		}
	}
	for x = (LastAddr + int16(LastLen)); x < 0x2000; x++ {
		data = 0xFF
		//fmt.Printf("x = %04x\n", x)
		for counter = 0; counter < 0x08; counter++ {
			if (data&0x80)^(crc&0x80) != 0x00 {
				crc = ((crc << 1) ^ crcPoly)
			} else {
				crc = (crc << 1)
			}
			data = data << 1
		}
	}
	CRCColor := color.New(color.FgGreen)
	CRCColor.EnableColor()
	fmt.Printf("\n\tCRC HEX file  : ")
	CRCColor.Printf("0x%02X\n\n", crc)
}

//CRCCompute Fonction calcul CRC
func CRCCompute(TC []byte, sizeTC int) byte {
	var crc byte = 0x00
	var crcPoly byte = 0xD5
	var data byte = 0x00
	var counter int = 0
	var counter2 byte = 0x00

	for counter = 0; counter < sizeTC; counter++ {
		data = TC[counter]

		for counter2 = 0; counter2 < 0x08; counter2++ {
			if (data&0x80)^(crc&0x80) != 0x00 {
				crc = ((crc << 1) ^ crcPoly)
			} else {
				crc = (crc << 1)
			}
			data = data << 1
		}
	}

	return crc
}

//TxUart Fonction TX UART
func TxUart(port *serial.Port, TC []byte, sizeTC int) {
	var crc byte = 0x00

	crc = CRCCompute(TC, sizeTC)

	buf := make([]byte, 1)

	for i := 0; i < (sizeTC + 1); i++ {
		if i == sizeTC {
			buf[0] = crc
		} else {
			buf[0] = TC[i]
		}
		_, err := port.Write(buf)

		// time.Sleep(1 * time.Millisecond)
		if err != nil {
			log.Fatalf("port.Write: %v", err)
		}
	}
	fmt.Printf("\n")
}

//TxUartClearWdG Fonction TX UART Clear WDG
func TxUartClearWdG(port *serial.Port) {
	for {
		if FlagClearWDG == 0xAA {
			b := []byte{0x12, 0x34, 0x00, 0x01, 0xa9} //1234008146
			for i := 0; i < len(b); i++ {
				c := []byte{b[i]}
				_, err := port.Write(c)
				time.Sleep(1 * time.Millisecond)
				if err != nil {
					log.Fatalf("port.Write: %v", err)
				}
			}
		}
		time.Sleep(250 * time.Millisecond)
	}
}

// LoadConfiguration chargement BD
func LoadConfiguration(file string) ([]BDstruct, error) {
	var config []BDstruct
	configFile, err := os.Open(file)
	defer configFile.Close()
	if err != nil {
		return config, err
	}
	jsonParser := json.NewDecoder(configFile)
	err = jsonParser.Decode(&config)
	return config, err
}

//FormattageTC encodeur TC
func FormattageTC(ListeTC []BDstruct, index int, s *serial.Port) ([]byte, int) {
	var tc []byte
	var crc byte
	var err int

	if index > len(ListeTC) {
		fmt.Printf("\nErreur, TC inconnue\n\n")
		err = 1
		return tc, err
	}

	tc = append(tc, byte(S2H(ListeTC[index].Header[:2])))
	tc = append(tc, byte(S2H(ListeTC[index].Header[2:4])))
	tc = append(tc, byte(S2H(ListeTC[index].Length)))
	tc = append(tc, byte(S2H(ListeTC[index].Tag)))

	if tc[2] != 0 {
		for _, w := range ListeTC[index].Data {
			if w[0] == "?" {

			} else if w[2] == "?" {
				var Choix string
				fmt.Printf("\n%s\n", w[1])
				fmt.Scanf("%s", &Choix)
				NbrOctet, _ := strconv.Atoi(w[0])
				for u := 0; u < NbrOctet; u++ {
					tc = append(tc, byte(S2H(Choix[2*u:(2*u)+2])))
				}
			} else {
				NbrOctet, _ := strconv.Atoi(w[0])
				for p := 0; p < NbrOctet; p++ {
					tc = append(tc, byte(S2H(w[2][2*p:(2*p)+2])))
				}
			}
		}
	}
	crc = CRCCompute(tc, len(tc))
	tc = append(tc, crc)

	return tc, err
}

//S2H fonction de conversion de string 2 byte
func S2H(liste string) int {
	var temp []byte
	temp, _ = hex.DecodeString(liste)
	return int(temp[0])
}

//MenuTC affiche la liste des TC
func MenuTC(listeTC []BDstruct) {
	fmt.Printf("\n\n************************************\n")
	for i, x := range listeTC {
		fmt.Printf("* %02d: %s (%s)", i+1, x.Name, x.Tag)
		for y := 0; y < (32 - len(x.Name) - 8); y++ {
			fmt.Printf(" ")
		}
		fmt.Printf("*\n")

		if i == len(listeTC) {
			fmt.Printf("* %02d: Quitter Menu TC", i+1)
			for y := 0; y < (32 - len(x.Name) - 8); y++ {
				fmt.Printf(" ")
			}
			fmt.Printf("*\n")
		}
	}
	fmt.Printf("************************************\n\n")
}

//RechargementAppliMRAM rechargement de l'applicartif en MRAM
func RechargementAppliMRAM(s *serial.Port) {
	var tc []byte
	var crc byte

	b := []byte{0x12, 0x34, 0x00, 0x8C, 0x44} //TC Erase MRAM Appli reload
	for i := 0; i < len(b); i++ {
		c := []byte{b[i]}
		_, err := s.Write(c)
		time.Sleep(1 * time.Millisecond)
		if err != nil {
			log.Fatalf("port.Write: %v", err)
		}
	}

	EraseColor := color.New(color.FgRed, color.Bold)
	EraseColor.EnableColor()
	EraseColor.Printf("\n\tEffacement en cours ...\n")
	time.Sleep(10 * time.Second)
	EraseColor.Printf("\n\n\tLe chargement va commencer ...\n\n")
	time.Sleep(1 * time.Second)

	file, err1 := os.Open("main.hex")
	if err1 != nil {
		log.Fatal(err1)
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)

	for scanner.Scan() { // internally, it advances token based on sperator
		var LineHex string
		var ByteLineHex [128]byte
		LineHex = scanner.Text()
		fmt.Printf("%s", LineHex)

		if LineHex[0] == ':' {
			for i := 0; i < ((len(LineHex) - 1) / 2); i++ {
				ByteLineHex[i] = byte(S2H(LineHex[1+(2*i) : 1+(2*i)+2]))
				//fmt.Printf("\n%x", ByteLineHex[i])
			}
			tc = nil
			tc = append(tc, byte(0x12))
			tc = append(tc, byte(0x34))
			tc = append(tc, ByteLineHex[0]+5)
			tc = append(tc, byte(0x0D))

			for i := 0; i < int(ByteLineHex[0]+5); i++ {
				tc = append(tc, ByteLineHex[i])
			}
			crc = CRCCompute(tc, len(tc))
			tc = append(tc, crc)

			TxUart(s, tc, len(tc))
			time.Sleep(10 * time.Millisecond)
		}
	}
}

//RechargementGOLDENMRAM rechargement du Golden en MRAM
func RechargementGOLDENMRAM(s *serial.Port) {
	var tc []byte
	var crc byte

	b := []byte{0x43, 0x21, 0x00, 0xCC, 0x44} //TC Erase MRAM Appli reload
	for i := 0; i < len(b); i++ {
		c := []byte{b[i]}
		_, err := s.Write(c)
		time.Sleep(1 * time.Millisecond)
		if err != nil {
			log.Fatalf("port.Write: %v", err)
		}
	}

	EraseColor := color.New(color.FgRed, color.Bold)
	EraseColor.EnableColor()
	EraseColor.Printf("\n\tEffacement en cours ...\n")
	time.Sleep(10 * time.Second)
	EraseColor.Printf("\n\n\tLe chargement va commencer ...\n\n")
	time.Sleep(1 * time.Second)

	file, err1 := os.Open("main.hex")
	if err1 != nil {
		log.Fatal(err1)
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)

	for scanner.Scan() { // internally, it advances token based on sperator
		var LineHex string
		var ByteLineHex [128]byte
		LineHex = scanner.Text()
		fmt.Printf("%s", LineHex)

		if LineHex[0] == ':' {
			for i := 0; i < ((len(LineHex) - 1) / 2); i++ {
				ByteLineHex[i] = byte(S2H(LineHex[1+(2*i) : 1+(2*i)+2]))
				//fmt.Printf("\n%x", ByteLineHex[i])
			}
			tc = nil
			tc = append(tc, byte(0x43))
			tc = append(tc, byte(0x21))
			tc = append(tc, ByteLineHex[0]+5)
			tc = append(tc, byte(0xCD))

			for i := 0; i < int(ByteLineHex[0]+5); i++ {
				tc = append(tc, ByteLineHex[i])
			}
			crc = CRCCompute(tc, len(tc))
			tc = append(tc, crc)

			TxUart(s, tc, len(tc))
			time.Sleep(10 * time.Millisecond)
		}
	}
}

func main() {
	fmt.Printf("\n\n\t******************\n\t**** UART SRU ****\n\t******************\n\n")

	FileTMptr := flag.String("TMFile", "Tmfile.txt", "fichier où sera stockée la TM reçue")
	flag.Parse()

	TMFile, errfileTM := os.OpenFile(*FileTMptr, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0777)

	defer TMFile.Close()
	if errfileTM != nil {
		fmt.Println("erreur TM file :", errfileTM)
	}

	c := &serial.Config{Name: "/dev/ttyUSB0", Baud: 57600}
	s, err := serial.OpenPort(c)
	if err != nil {
		log.Fatal(err)
	}

	// Make sure to close it later.
	defer s.Close()

	ListeTC, _ = LoadConfiguration("BDTC.json")
	ListeTM, _ = LoadConfiguration("BDTM.json")
	for i := 0; i < len(ListeTM); i++ {
		IndexationTM[S2H(ListeTM[i].Tag)] = i
	}

	go RxUART(s)
	//go TxUartClearWdG(s)

	for {
		var Choix string
		var Choixint int

		fmt.Println("\n********\n* Menu *\n********\n")
		fmt.Println("01 : Envoie de TC")
		fmt.Println("02 : Liste des TC")
		fmt.Println("03 : Liste des TM")
		fmt.Println("04 : Calcul du CRC du fichier main.hex (Appli SRU)")
		fmt.Println("05 : Rechargement Applicatif in MRAM")
		fmt.Println("06 : Dump, calcul et comparaison des CRC du fichier DUMP_Appli_file.txt et main.hex (Appli SRU in MRAM)")
		fmt.Println("10 : Enable Clear_WDG")
		fmt.Println("11 : Disable Clear_WDG")
		fmt.Println("99 : Quitter\n")

		fmt.Scanln(&Choix)
		Choixint, _ = strconv.Atoi(Choix)

		if Choixint == 1 {
			var Choix2 string

			MenuTC(ListeTC)
			fmt.Scanln(&Choix2)

			Choix2int, _ := strconv.Atoi(Choix2)

			for Choix2int != 99 && Choix2int < len(ListeTC) {
				if Choix2int != 0 {
					tc, err := FormattageTC(ListeTC, Choix2int-1, s)

					tc = append(tc, 0x00)
					if err != 0 {
						fmt.Printf("\nError : %d\n", err)
					}

					NewTC := color.New(color.FgCyan, color.Bold)
					NewTC.EnableColor()
					NewTC.Printf("\n - TC Send : %s - :", ListeTC[Choix2int-1].Name)

					HeaderColor := color.New(color.FgHiMagenta)
					LenColor := color.New(color.FgHiYellow)
					TagColor := color.New(color.FgHiBlue)
					DataRawColor := color.New(color.FgHiGreen)
					CRCColor := color.New(color.FgHiRed)

					HeaderColor.EnableColor()
					LenColor.EnableColor()
					TagColor.EnableColor()
					DataRawColor.EnableColor()
					CRCColor.EnableColor()

					for h := 0; h < int(tc[2]+5); h++ {
						if h < 2 {
							HeaderColor.Printf(" 0x%02X", tc[h])
						} else if h == 2 {
							LenColor.Printf(" 0x%02X", tc[h])
						} else if h == 3 {
							TagColor.Printf(" 0x%02X", tc[h])
						} else if h > 3 && h != int(tc[2]+4) {
							DataRawColor.Printf(" 0x%02X", tc[h])
						} else {
							CRCColor.Printf(" 0x%02X", tc[h])
						}
					}
					TxUart(s, tc, len(tc))

					for i := 0; i < 100; i++ {
						TxUart(s, tc, len(tc))
						time.Sleep(5 * time.Millisecond)
					}

				} else {
					MenuTC(ListeTC)
				}
				Choix2int = 0
				Choix2 = ""
				fmt.Scanln(&Choix2)
				Choix2int, _ = strconv.Atoi(Choix2)
			}
		} else if Choixint == 2 {
			MenuTC(ListeTC)
		} else if Choixint == 3 {
			fmt.Printf("\n\n*************************************\n")
			for i, x := range ListeTM {
				fmt.Printf("* %02d: %s (%s)", i, x.Name, x.Tag)
				for y := 0; y < (32 - len(x.Name) - 7); y++ {
					fmt.Printf(" ")
				}
				fmt.Printf("*\n")
			}
			fmt.Printf("*************************************\n\n")
		} else if Choixint == 4 {
			ComputeCRCHEX()
		} else if Choixint == 5 {
			RechargementAppliMRAM(s)
		} else if Choixint == 6 {
			b := []byte{0x12, 0x34, 0x00, 0x8E, 0x3b} //TC Erase MRAM Appli reload
			for i := 0; i < len(b); i++ {
				c := []byte{b[i]}
				_, err := s.Write(c)
				time.Sleep(1 * time.Millisecond)
				if err != nil {
					log.Fatalf("port.Write: %v", err)
				}
			}
			time.Sleep(8 * time.Second)
			ComputeCRCDUMP()
			ComputeCRCHEX()
		} else if Choixint == 7 {
			RechargementGOLDENMRAM(s)
		} else if Choixint == 10 {
			FlagClearWDG = 0xAA
		} else if Choixint == 11 {
			FlagClearWDG = 0x55
		} else if Choixint == 99 {
			fmt.Println("Bye bye")
			return
		}

		Choixint = 0
		Choix = ""
	}
}
